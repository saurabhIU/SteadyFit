"""Long-term memory: multi-user profiles + adherence (Postgres / Neon)."""
from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, cast
from zoneinfo import ZoneInfo

import psycopg
from psycopg import Connection
from psycopg.rows import DictRow, dict_row

from app.config import settings
from app.graph.state import UserProfile, WeekPlan

_SLUG_RE = re.compile(r"[^a-z0-9]+")
TRY_TTL_HOURS = 48
KB_DOC_TYPES = ["kb_exercise", "kb_guide", "kb_template", "kb_science"]


def _conn() -> Connection[DictRow]:
    """Open a dict-row connection.

    psycopg stubs type ``connect()`` / ``row_factory`` as ``TupleRow``-only, so we
    avoid ``row_factory=`` on connect and assign ``dict_row`` via ``Any``.
    """
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set")
    conn = psycopg.connect(settings.database_url)
    conn.row_factory = cast(Any, dict_row)
    return cast(Connection[DictRow], conn)


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def slugify_name(name: str) -> str:
    base = _SLUG_RE.sub("-", name.strip().lower()).strip("-") or "user"
    return base[:40]


def create_user(name: str, user_id: str | None = None) -> str:
    """Create blank onboarding profile. Returns user_id."""
    uid = user_id or f"{slugify_name(name)}-{uuid.uuid4().hex[:6]}"
    with _conn() as c:
        c.execute(
            "INSERT INTO app_users(user_id, name) VALUES (%s, %s)",
            (uid, name.strip() or "athlete"),
        )
        c.execute(
            """
            INSERT INTO user_profiles(
                user_id, name, goal, onboarding_complete, awaiting_onboarding_confirm,
                is_ephemeral, expires_at
            ) VALUES (%s, %s, '', FALSE, FALSE, FALSE, NULL)
            """,
            (uid, name.strip() or "athlete"),
        )
        c.commit()
    return uid


def create_try_user() -> str:
    """Public no-login session: try-<8hex>, ephemeral, expires in 48h."""
    uid = f"try-{uuid.uuid4().hex[:8]}"
    expires = datetime.now(timezone.utc) + timedelta(hours=TRY_TTL_HOURS)
    with _conn() as c:
        c.execute(
            "INSERT INTO app_users(user_id, name) VALUES (%s, %s)",
            (uid, "Guest"),
        )
        c.execute(
            """
            INSERT INTO user_profiles(
                user_id, name, goal, onboarding_complete, awaiting_onboarding_confirm,
                is_ephemeral, expires_at
            ) VALUES (%s, %s, '', FALSE, FALSE, TRUE, %s)
            """,
            (uid, "Guest", expires),
        )
        c.commit()
    return uid


def user_exists(user_id: str) -> bool:
    with _conn() as c:
        row = c.execute(
            "SELECT 1 FROM app_users WHERE user_id = %s", (user_id,)
        ).fetchone()
    return row is not None


def list_users(*, include_ephemeral: bool = True) -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            """
            SELECT u.user_id, u.name, u.created_at,
                   p.goal, p.onboarding_complete,
                   COALESCE(p.is_ephemeral, FALSE) AS is_ephemeral,
                   p.expires_at
            FROM app_users u
            LEFT JOIN user_profiles p ON p.user_id = u.user_id
            WHERE (%s OR COALESCE(p.is_ephemeral, FALSE) = FALSE)
            ORDER BY u.created_at ASC
            """,
            (include_ephemeral,),
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "user_id": r["user_id"],
            "name": r["name"],
            "goal": r.get("goal") or "",
            "onboarding_complete": bool(r.get("onboarding_complete")),
            "is_ephemeral": bool(r.get("is_ephemeral")),
            "expires_at": (
                r["expires_at"].isoformat() if r.get("expires_at") else None
            ),
            "created_at": (
                r["created_at"].isoformat() if r.get("created_at") else None
            ),
        })
    return out


def list_users_for_weekly_review() -> list[dict[str, Any]]:
    """Stable profiles only — never run Sunday cron on try-* guests."""
    return list_users(include_ephemeral=False)


def ensure_user(user_id: str, name: str | None = None) -> str:
    """Idempotent create for seed scripts."""
    if user_exists(user_id):
        return user_id
    return create_user(name or user_id, user_id=user_id)


def log_workout(
    user_id: str,
    date_str: str,
    focus: str,
    status: str,
    *,
    source: str | None = None,
):
    with _conn() as c:
        # Idempotent for DBs created before source column existed.
        c.execute("ALTER TABLE workout_log ADD COLUMN IF NOT EXISTS source TEXT")
        c.execute(
            """
            INSERT INTO workout_log(user_id, date, focus, status, source)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (user_id, date_str[:10], focus, status, source),
        )
        c.commit()


def get_workouts_on(user_id: str, date_str: str) -> list[dict]:
    """Workout log rows for a single calendar day (newest first)."""
    with _conn() as c:
        c.execute("ALTER TABLE workout_log ADD COLUMN IF NOT EXISTS source TEXT")
        rows = c.execute(
            """
            SELECT date::text AS date, focus, status, source, id
            FROM workout_log
            WHERE user_id = %s AND date = %s
            ORDER BY id DESC
            """,
            (user_id, date_str[:10]),
        ).fetchall()
    return [
        {
            "date": r["date"][:10],
            "focus": r["focus"],
            "status": r["status"],
            "source": r.get("source"),
            "id": r["id"],
        }
        for r in rows
    ]


def log_weight(user_id: str, date_str: str, kg: float):
    with _conn() as c:
        c.execute(
            "INSERT INTO weight_log(user_id, date, kg) VALUES (%s,%s,%s)",
            (user_id, date_str[:10], kg),
        )
        c.commit()


def get_workouts_between(user_id: str, start: date, end: date) -> list[dict]:
    with _conn() as c:
        c.execute("ALTER TABLE workout_log ADD COLUMN IF NOT EXISTS source TEXT")
        rows = c.execute(
            """
            SELECT date::text AS date, focus, status, source, id
            FROM workout_log
            WHERE user_id = %s AND date >= %s AND date < %s
            ORDER BY date ASC, id ASC
            """,
            (user_id, start.isoformat(), end.isoformat()),
        ).fetchall()
    return [
        {
            "date": r["date"][:10],
            "focus": r["focus"],
            "status": r["status"],
            "source": r.get("source"),
            "id": r["id"],
        }
        for r in rows
    ]


def get_week_workout_logs(user_id: str, week_start: str | None = None) -> list[dict]:
    """Workout log rows for the Mon–Sun week containing week_start (or this week)."""
    if week_start:
        start = date.fromisoformat(week_start[:10])
    else:
        start = _week_start(date.today())
    end = start + timedelta(days=7)
    return get_workouts_between(user_id, start, end)


def list_workout_week_starts(user_id: str) -> list[date]:
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT date FROM workout_log WHERE user_id = %s",
            (user_id,),
        ).fetchall()
    weeks: set[date] = set()
    for r in rows:
        d = r["date"]
        if isinstance(d, date):
            weeks.add(_week_start(d))
        else:
            try:
                weeks.add(_week_start(date.fromisoformat(str(d)[:10])))
            except ValueError:
                continue
    return sorted(weeks)


def _weekly_done_counts(user_id: str) -> dict[date, int]:
    weekly_days: dict[date, set[str]] = {}
    with _conn() as c:
        rows = c.execute(
            "SELECT date, status FROM workout_log WHERE user_id = %s",
            (user_id,),
        ).fetchall()
    for r in rows:
        if r["status"] != "done":
            continue
        d = r["date"]
        if not isinstance(d, date):
            try:
                d = date.fromisoformat(str(d)[:10])
            except ValueError:
                continue
        ws = _week_start(d)
        weekly_days.setdefault(ws, set()).add(d.isoformat())
    return {ws: len(days) for ws, days in weekly_days.items()}


def _streak_threshold(sessions_per_week: int) -> int:
    return max(1, (sessions_per_week * 3 + 4) // 5)


def get_week_streak(
    user_id: str,
    sessions_per_week: int = 3,
    *,
    as_of: date | None = None,
) -> int:
    threshold = _streak_threshold(sessions_per_week)
    weekly = _weekly_done_counts(user_id)
    if not weekly:
        return 0
    today = as_of or date.today()
    this_week = _week_start(today)
    week = this_week
    streak = 0
    for _ in range(52):
        done = weekly.get(week, 0)
        if done >= threshold:
            streak += 1
            week -= timedelta(days=7)
        elif week == this_week:
            week -= timedelta(days=7)
        else:
            break
    return streak


def get_adherence_stats(user_id: str) -> dict:
    profile = get_profile(user_id)
    sessions = profile.sessions_per_week or 3
    with _conn() as c:
        rows = c.execute(
            """
            SELECT status, COUNT(*)::int AS n FROM workout_log
            WHERE user_id = %s AND date >= (CURRENT_DATE - INTERVAL '14 days')
            GROUP BY status
            """,
            (user_id,),
        ).fetchall()
    stats = {r["status"]: r["n"] for r in rows}
    done, skipped = stats.get("done", 0), stats.get("skipped", 0)
    total = done + skipped
    return {
        "last14d": stats,
        "adherence_pct": round(100 * done / total) if total else None,
        "drop_off_signal": skipped >= 3,
        "streak_weeks": get_week_streak(user_id, sessions),
    }


def get_profile(user_id: str) -> UserProfile:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM user_profiles WHERE user_id = %s", (user_id,)
        ).fetchone()
    if not row:
        return UserProfile()
    modes = row.get("preferred_workout_modes") or []
    constraints = row.get("constraints") or []
    if isinstance(modes, str):
        modes = json.loads(modes)
    if isinstance(constraints, str):
        constraints = json.loads(constraints)
    return UserProfile(
        name=row.get("name") or "athlete",
        goal=row.get("goal") or "",
        age=row.get("age"),
        age_declined=bool(row.get("age_declined")),
        sex=row.get("sex"),
        sex_declined=bool(row.get("sex_declined")),
        weight_kg=float(row["weight_kg"]) if row.get("weight_kg") is not None else None,
        weight_declined=bool(row.get("weight_declined")),
        target_weight_kg=(
            float(row["target_weight_kg"]) if row.get("target_weight_kg") is not None else None
        ),
        target_weight_declined=bool(row.get("target_weight_declined")),
        height_cm=float(row["height_cm"]) if row.get("height_cm") is not None else None,
        height_declined=bool(row.get("height_declined")),
        activity_level=row.get("activity_level"),
        activity_declined=bool(row.get("activity_declined")),
        preferred_workout_modes=list(modes),
        food_preference=row.get("food_preference"),
        sessions_per_week=row.get("sessions_per_week"),
        constraints=list(constraints),
        constraints_asked=bool(row.get("constraints_asked")),
        onboarding_complete=bool(row.get("onboarding_complete")),
        awaiting_onboarding_confirm=bool(row.get("awaiting_onboarding_confirm")),
        awaiting_weight_for_first_plan=bool(row.get("awaiting_weight_for_first_plan")),
        awaiting_diet_slot=row.get("awaiting_diet_slot"),
        shown_upload_hint=bool(row.get("shown_upload_hint")),
        offered_upload_before_weight_gate=bool(
            row.get("offered_upload_before_weight_gate")
        ),
        awaiting_upload_before_weight=bool(row.get("awaiting_upload_before_weight")),
    )


def save_profile(user_id: str, profile: UserProfile):
    ensure_user(user_id, profile.name)
    with _conn() as c:
        c.execute(
            """
            INSERT INTO user_profiles (
                user_id, name, goal, age, age_declined, sex, sex_declined,
                weight_kg, weight_declined, target_weight_kg, target_weight_declined,
                height_cm, height_declined, activity_level, activity_declined,
                preferred_workout_modes, food_preference,
                sessions_per_week, constraints, constraints_asked, onboarding_complete,
                awaiting_onboarding_confirm, awaiting_weight_for_first_plan,
                awaiting_diet_slot, shown_upload_hint,
                offered_upload_before_weight_gate, awaiting_upload_before_weight,
                updated_at
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s::jsonb,
                %s,%s,%s,%s,%s,%s,%s,%s, now()
            )
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name,
                goal = EXCLUDED.goal,
                age = EXCLUDED.age,
                age_declined = EXCLUDED.age_declined,
                sex = EXCLUDED.sex,
                sex_declined = EXCLUDED.sex_declined,
                weight_kg = EXCLUDED.weight_kg,
                weight_declined = EXCLUDED.weight_declined,
                target_weight_kg = EXCLUDED.target_weight_kg,
                target_weight_declined = EXCLUDED.target_weight_declined,
                height_cm = EXCLUDED.height_cm,
                height_declined = EXCLUDED.height_declined,
                activity_level = EXCLUDED.activity_level,
                activity_declined = EXCLUDED.activity_declined,
                preferred_workout_modes = EXCLUDED.preferred_workout_modes,
                food_preference = EXCLUDED.food_preference,
                sessions_per_week = EXCLUDED.sessions_per_week,
                constraints = EXCLUDED.constraints,
                constraints_asked = EXCLUDED.constraints_asked,
                onboarding_complete = EXCLUDED.onboarding_complete,
                awaiting_onboarding_confirm = EXCLUDED.awaiting_onboarding_confirm,
                awaiting_weight_for_first_plan = EXCLUDED.awaiting_weight_for_first_plan,
                awaiting_diet_slot = EXCLUDED.awaiting_diet_slot,
                shown_upload_hint = EXCLUDED.shown_upload_hint,
                offered_upload_before_weight_gate = EXCLUDED.offered_upload_before_weight_gate,
                awaiting_upload_before_weight = EXCLUDED.awaiting_upload_before_weight,
                updated_at = now()
            """,
            (
                user_id,
                profile.name,
                profile.goal,
                profile.age,
                profile.age_declined,
                profile.sex,
                profile.sex_declined,
                profile.weight_kg,
                profile.weight_declined,
                profile.target_weight_kg,
                profile.target_weight_declined,
                profile.height_cm,
                profile.height_declined,
                profile.activity_level,
                profile.activity_declined,
                json.dumps(profile.preferred_workout_modes),
                profile.food_preference,
                profile.sessions_per_week,
                json.dumps(profile.constraints),
                profile.constraints_asked,
                profile.onboarding_complete,
                profile.awaiting_onboarding_confirm,
                profile.awaiting_weight_for_first_plan,
                profile.awaiting_diet_slot,
                profile.shown_upload_hint,
                profile.offered_upload_before_weight_gate,
                profile.awaiting_upload_before_weight,
            ),
        )
        c.execute(
            "UPDATE app_users SET name = %s WHERE user_id = %s",
            (profile.name, user_id),
        )
        c.commit()


def user_has_personal_docs(user_id: str) -> bool:
    """True when the user has at least one uploaded personal document chunk."""
    if not user_id:
        return False
    personal_types = ("personal", "program", "recipes", "reference", "knowledge")
    with _conn() as c:
        row = c.execute(
            """
            SELECT 1 AS ok
            FROM documents
            WHERE user_id = %s AND doc_type = ANY(%s)
            LIMIT 1
            """,
            (user_id, list(personal_types)),
        ).fetchone()
    return bool(row)


def get_saved_week_plan(user_id: str) -> WeekPlan | None:
    with _conn() as c:
        row = c.execute(
            """
            SELECT plan FROM week_plans
            WHERE user_id = %s AND is_current
            ORDER BY week_start DESC LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    if not row:
        return None
    try:
        return WeekPlan(**(row["plan"] if isinstance(row["plan"], dict) else json.loads(row["plan"])))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def save_week_plan(user_id: str, plan: WeekPlan | dict):
    payload = plan.model_dump() if isinstance(plan, WeekPlan) else plan
    week_start = str(payload.get("week_start", ""))[:10]
    if not week_start:
        raise ValueError("week_plan missing week_start")
    with _conn() as c:
        c.execute(
            "UPDATE week_plans SET is_current = FALSE WHERE user_id = %s",
            (user_id,),
        )
        c.execute(
            """
            INSERT INTO week_plans(user_id, week_start, plan, is_current)
            VALUES (%s, %s, %s::jsonb, TRUE)
            ON CONFLICT (user_id, week_start) DO UPDATE SET
                plan = EXCLUDED.plan,
                is_current = TRUE
            """,
            (user_id, week_start, json.dumps(payload)),
        )
        c.commit()


def clear_current_week_plan(user_id: str) -> None:
    """Mark any current week plan as not current (first-plan evals)."""
    with _conn() as c:
        c.execute(
            "UPDATE week_plans SET is_current = FALSE WHERE user_id = %s",
            (user_id,),
        )
        c.commit()


def log_food_entry(
    user_id: str,
    *,
    foods: list[dict] | list,
    kcal: float | None = None,
    protein_g: float | None = None,
    carbs_g: float | None = None,
    fat_g: float | None = None,
    source: str = "text",
    meal_label: str | None = None,
    notes: str | None = None,
) -> int:
    """Persist structured meal summary only — never store images."""
    src = source if source in {"text", "photo"} else "text"
    with _conn() as c:
        row = c.execute(
            """
            INSERT INTO food_log (
                user_id, meal_label, foods, kcal, protein_g, carbs_g, fat_g, source, notes
            ) VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                meal_label,
                json.dumps(list(foods)),
                kcal,
                protein_g,
                carbs_g,
                fat_g,
                src,
                notes,
            ),
        ).fetchone()
        c.commit()
    return int(row["id"])


def recent_food_logs(user_id: str, *, limit: int = 10) -> list[dict]:
    """Raw recent rows — does not sum. Prefer get_daily_totals for day intake."""
    with _conn() as c:
        rows = c.execute(
            """
            SELECT id, logged_at, meal_label, foods, kcal, protein_g, carbs_g, fat_g,
                   source, notes
            FROM food_log
            WHERE user_id = %s
            ORDER BY logged_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        ).fetchall()
    out = []
    for r in rows:
        foods = r["foods"]
        if isinstance(foods, str):
            foods = json.loads(foods)
        out.append({
            "id": r["id"],
            "logged_at": r["logged_at"].isoformat() if r.get("logged_at") else None,
            "meal_label": r.get("meal_label"),
            "foods": foods,
            "kcal": r.get("kcal"),
            "protein_g": r.get("protein_g"),
            "carbs_g": r.get("carbs_g"),
            "fat_g": r.get("fat_g"),
            "source": r.get("source") or "text",
            "notes": r.get("notes"),
        })
    return out


def _day_window(
    day: date | None = None,
    *,
    tz: str = "UTC",
) -> tuple[date, str, datetime, datetime]:
    """Resolve calendar day + timezone-aware [start, end) for food_log filters."""
    try:
        zone = ZoneInfo(tz)
    except Exception:
        zone = ZoneInfo("UTC")
        tz = "UTC"
    if day is None:
        day = datetime.now(zone).date()
    start = datetime.combine(day, time.min, tzinfo=zone)
    end = start + timedelta(days=1)
    return day, tz, start, end


def food_logs_for_day(
    user_id: str,
    day: date | None = None,
    *,
    tz: str = "UTC",
) -> list[dict]:
    """Today's (or given day's) food_log rows — same day boundary as get_daily_totals."""
    _day, _tz, start, end = _day_window(day, tz=tz)
    with _conn() as c:
        rows = c.execute(
            """
            SELECT id, logged_at, meal_label, foods, kcal, protein_g, carbs_g, fat_g,
                   source, notes
            FROM food_log
            WHERE user_id = %s
              AND logged_at >= %s
              AND logged_at < %s
            ORDER BY logged_at ASC
            """,
            (user_id, start, end),
        ).fetchall()
    out = []
    for r in rows:
        foods = r["foods"]
        if isinstance(foods, str):
            foods = json.loads(foods)
        out.append({
            "id": r["id"],
            "logged_at": r["logged_at"].isoformat() if r.get("logged_at") else None,
            "meal_label": r.get("meal_label"),
            "foods": foods,
            "kcal": r.get("kcal"),
            "protein_g": r.get("protein_g"),
            "carbs_g": r.get("carbs_g"),
            "fat_g": r.get("fat_g"),
            "source": r.get("source") or "text",
            "notes": r.get("notes"),
        })
    return out


def get_daily_totals(
    user_id: str,
    day: date | None = None,
    *,
    tz: str = "UTC",
) -> dict[str, Any]:
    """Sum food_log macros for one calendar day (timezone-aware day boundary).

    Day filter uses logged_at half-open interval [local midnight, next midnight)
    so Neon TIMESTAMPTZ rows map correctly. Defaults to "today" in ``tz``.
    """
    day, tz, start, end = _day_window(day, tz=tz)
    with _conn() as c:
        row = c.execute(
            """
            SELECT
                COALESCE(SUM(kcal), 0)::real AS kcal_consumed,
                COALESCE(SUM(protein_g), 0)::real AS protein_g_consumed,
                COALESCE(SUM(carbs_g), 0)::real AS carbs_g_consumed,
                COALESCE(SUM(fat_g), 0)::real AS fat_g_consumed,
                COUNT(*)::int AS entry_count
            FROM food_log
            WHERE user_id = %s
              AND logged_at >= %s
              AND logged_at < %s
            """,
            (user_id, start, end),
        ).fetchone()
    return {
        "date": day.isoformat(),
        "tz": tz,
        "kcal_consumed": float(row["kcal_consumed"] or 0) if row else 0.0,
        "protein_g_consumed": float(row["protein_g_consumed"] or 0) if row else 0.0,
        "carbs_g_consumed": float(row["carbs_g_consumed"] or 0) if row else 0.0,
        "fat_g_consumed": float(row["fat_g_consumed"] or 0) if row else 0.0,
        "entry_count": int(row["entry_count"] or 0) if row else 0,
    }


def today_food_log_snapshot(
    user_id: str,
    *,
    calorie_target: int | None = None,
    protein_target_g: int | None = None,
    tz: str = "UTC",
    week_start: str | None = None,
) -> dict[str, Any]:
    """Meals + totals + plan targets for the Plan page (display-only)."""
    meals = food_logs_for_day(user_id, tz=tz)
    totals = get_daily_totals(user_id, tz=tz)
    planned = diet_meals_for_day(user_id, day=None, tz=tz, week_start=week_start)
    return {
        "meals": [
            {
                "id": m["id"],
                "meal_label": m.get("meal_label"),
                "foods": m.get("foods") or [],
                "kcal": m.get("kcal"),
                "protein_g": m.get("protein_g"),
                "logged_at": m.get("logged_at"),
            }
            for m in meals
        ],
        "planned_meals": planned,
        "totals": totals,
        "targets": {
            "calorie_target": calorie_target,
            "protein_target_g": protein_target_g,
        },
    }


def replace_diet_plan_week(
    user_id: str,
    week_start: str,
    meals: list[dict[str, Any]],
) -> int:
    """Replace diet_plan_days for a week with structured meal rows."""
    with _conn() as c:
        c.execute(
            "DELETE FROM diet_plan_days WHERE user_id = %s AND week_start = %s",
            (user_id, week_start),
        )
        n = 0
        for m in meals:
            c.execute(
                """
                INSERT INTO diet_plan_days (
                    user_id, week_start, day, meal_slot, food_description,
                    kcal, protein_g, status, source_kb_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    week_start,
                    m.get("day") or "",
                    m.get("meal_slot") or "meal",
                    m.get("food_description") or "",
                    m.get("kcal"),
                    m.get("protein_g"),
                    m.get("status") or "planned",
                    m.get("source_kb_id"),
                ),
            )
            n += 1
        c.commit()
    return n


def diet_meals_for_week(user_id: str, week_start: str) -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            """
            SELECT id, week_start, day, meal_slot, food_description, kcal, protein_g,
                   status, source_kb_id
            FROM diet_plan_days
            WHERE user_id = %s AND week_start = %s
            ORDER BY
              CASE day
                WHEN 'Mon' THEN 1 WHEN 'Tue' THEN 2 WHEN 'Wed' THEN 3
                WHEN 'Thu' THEN 4 WHEN 'Fri' THEN 5 WHEN 'Sat' THEN 6
                WHEN 'Sun' THEN 7 ELSE 8 END,
              CASE meal_slot
                WHEN 'breakfast' THEN 1 WHEN 'lunch' THEN 2
                WHEN 'dinner' THEN 3 WHEN 'snack' THEN 4 ELSE 5 END
            """,
            (user_id, week_start),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "week_start": str(r["week_start"]),
            "day": r["day"],
            "meal_slot": r["meal_slot"],
            "food_description": r["food_description"],
            "kcal": r.get("kcal"),
            "protein_g": r.get("protein_g"),
            "status": r.get("status") or "planned",
            "source_kb_id": r.get("source_kb_id"),
        }
        for r in rows
    ]


def diet_meals_for_day(
    user_id: str,
    day: date | None = None,
    *,
    tz: str = "UTC",
    week_start: str | None = None,
) -> list[dict[str, Any]]:
    """Planned diet meals for a calendar day (weekday abbr + week_start).

    Prefer the caller's week_start (usually the saved WeekPlan.week_start) so
    planned meals stay aligned with the approved plan week.
    """
    day_resolved, _tz, _start, _end = _day_window(day, tz=tz)
    abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day_resolved.weekday()]
    ws = (week_start or "").strip()[:10] or _week_start(day_resolved).isoformat()
    with _conn() as c:
        rows = c.execute(
            """
            SELECT id, week_start, day, meal_slot, food_description, kcal, protein_g,
                   status, source_kb_id
            FROM diet_plan_days
            WHERE user_id = %s AND week_start = %s AND day = %s
            ORDER BY
              CASE meal_slot
                WHEN 'breakfast' THEN 1 WHEN 'lunch' THEN 2
                WHEN 'dinner' THEN 3 WHEN 'snack' THEN 4 ELSE 5 END
            """,
            (user_id, ws, abbr),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "week_start": str(r["week_start"]),
            "day": r["day"],
            "meal_slot": r["meal_slot"],
            "food_description": r["food_description"],
            "kcal": r.get("kcal"),
            "protein_g": r.get("protein_g"),
            "status": r.get("status") or "planned",
            "source_kb_id": r.get("source_kb_id"),
        }
        for r in rows
    ]


def clear_profile_slots(user_id: str):
    """Reset profile fields for re-onboarding; keep logs/plans unless reset_user."""
    save_profile(
        user_id,
        UserProfile(
            name=get_profile(user_id).name or "athlete",
            onboarding_complete=False,
            awaiting_onboarding_confirm=False,
        ),
    )


def is_ephemeral_user(user_id: str) -> bool:
    with _conn() as c:
        row = c.execute(
            """
            SELECT COALESCE(is_ephemeral, FALSE) AS is_ephemeral
            FROM user_profiles WHERE user_id = %s
            """,
            (user_id,),
        ).fetchone()
    return bool(row and row.get("is_ephemeral"))


def _delete_user_data(c: Connection[DictRow], user_id: str) -> None:
    """Wipe logs/plans/non-kb docs/checkpointer threads for one user."""
    c.execute("DELETE FROM workout_log WHERE user_id = %s", (user_id,))
    c.execute("DELETE FROM weight_log WHERE user_id = %s", (user_id,))
    c.execute("DELETE FROM week_plans WHERE user_id = %s", (user_id,))
    c.execute(
        "DELETE FROM documents WHERE user_id = %s AND doc_type <> ALL(%s)",
        (user_id, KB_DOC_TYPES),
    )
    for table in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
        try:
            c.execute(
                f"DELETE FROM {table} WHERE thread_id LIKE %s",  # noqa: S608
                (f"{user_id}:%",),
            )
        except Exception:
            pass


def delete_user(user_id: str) -> None:
    """Hard-delete one user and all non-kb data (CASCADE clears user_profiles)."""
    if not user_exists(user_id):
        raise KeyError(user_id)
    with _conn() as c:
        _delete_user_data(c, user_id)
        c.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
        c.execute("DELETE FROM app_users WHERE user_id = %s", (user_id,))
        c.commit()


def delete_expired_ephemeral_users() -> list[str]:
    """Delete try-profiles past expires_at. Never touches is_ephemeral=false."""
    with _conn() as c:
        rows = c.execute(
            """
            SELECT user_id FROM user_profiles
            WHERE is_ephemeral = TRUE
              AND expires_at IS NOT NULL
              AND expires_at < now()
            """
        ).fetchall()
    deleted: list[str] = []
    for r in rows:
        uid = r["user_id"]
        delete_user(uid)
        deleted.append(uid)
    return deleted


def reset_user(user_id: str) -> None:
    """Wipe one profile's rows (not kb_*). Leaves app_users + blank profile."""
    if not user_exists(user_id):
        raise KeyError(user_id)
    name = get_profile(user_id).name or user_id
    ephemeral = is_ephemeral_user(user_id)
    expires_at = None
    if ephemeral:
        with _conn() as c:
            row = c.execute(
                "SELECT expires_at FROM user_profiles WHERE user_id = %s",
                (user_id,),
            ).fetchone()
        expires_at = row["expires_at"] if row else None
    with _conn() as c:
        _delete_user_data(c, user_id)
        c.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
        c.execute(
            """
            INSERT INTO user_profiles(
                user_id, name, goal, onboarding_complete, awaiting_onboarding_confirm,
                is_ephemeral, expires_at
            ) VALUES (%s, %s, '', FALSE, FALSE, %s, %s)
            """,
            (user_id, name, ephemeral, expires_at),
        )
        c.commit()

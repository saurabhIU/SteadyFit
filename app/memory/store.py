"""Long-term memory: multi-user profiles + adherence (Postgres / Neon)."""
from __future__ import annotations

import json
import re
import uuid
from datetime import date, timedelta
from typing import Any, cast

import psycopg
from psycopg import Connection
from psycopg.rows import DictRow, dict_row

from app.config import settings
from app.graph.state import UserProfile, WeekPlan

_SLUG_RE = re.compile(r"[^a-z0-9]+")


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
                user_id, name, goal, onboarding_complete, awaiting_onboarding_confirm
            ) VALUES (%s, %s, '', FALSE, FALSE)
            """,
            (uid, name.strip() or "athlete"),
        )
        c.commit()
    return uid


def user_exists(user_id: str) -> bool:
    with _conn() as c:
        row = c.execute(
            "SELECT 1 FROM app_users WHERE user_id = %s", (user_id,)
        ).fetchone()
    return row is not None


def list_users() -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            """
            SELECT u.user_id, u.name, u.created_at,
                   p.goal, p.onboarding_complete
            FROM app_users u
            LEFT JOIN user_profiles p ON p.user_id = u.user_id
            ORDER BY u.created_at ASC
            """
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "user_id": r["user_id"],
            "name": r["name"],
            "goal": r.get("goal") or "",
            "onboarding_complete": bool(r.get("onboarding_complete")),
            "created_at": (
                r["created_at"].isoformat() if r.get("created_at") else None
            ),
        })
    return out


def ensure_user(user_id: str, name: str | None = None) -> str:
    """Idempotent create for seed scripts."""
    if user_exists(user_id):
        return user_id
    return create_user(name or user_id, user_id=user_id)


def log_workout(user_id: str, date_str: str, focus: str, status: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO workout_log(user_id, date, focus, status) VALUES (%s,%s,%s,%s)",
            (user_id, date_str[:10], focus, status),
        )
        c.commit()


def log_weight(user_id: str, date_str: str, kg: float):
    with _conn() as c:
        c.execute(
            "INSERT INTO weight_log(user_id, date, kg) VALUES (%s,%s,%s)",
            (user_id, date_str[:10], kg),
        )
        c.commit()


def get_workouts_between(user_id: str, start: date, end: date) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            """
            SELECT date::text AS date, focus, status FROM workout_log
            WHERE user_id = %s AND date >= %s AND date < %s
            ORDER BY date
            """,
            (user_id, start.isoformat(), end.isoformat()),
        ).fetchall()
    return [{"date": r["date"][:10], "focus": r["focus"], "status": r["status"]} for r in rows]


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
        preferred_workout_modes=list(modes),
        food_preference=row.get("food_preference"),
        sessions_per_week=row.get("sessions_per_week"),
        constraints=list(constraints),
        constraints_asked=bool(row.get("constraints_asked")),
        onboarding_complete=bool(row.get("onboarding_complete")),
        awaiting_onboarding_confirm=bool(row.get("awaiting_onboarding_confirm")),
    )


def save_profile(user_id: str, profile: UserProfile):
    ensure_user(user_id, profile.name)
    with _conn() as c:
        c.execute(
            """
            INSERT INTO user_profiles (
                user_id, name, goal, age, age_declined, sex, sex_declined,
                preferred_workout_modes, food_preference, sessions_per_week,
                constraints, constraints_asked, onboarding_complete,
                awaiting_onboarding_confirm, updated_at
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s::jsonb,%s,%s,%s, now()
            )
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name,
                goal = EXCLUDED.goal,
                age = EXCLUDED.age,
                age_declined = EXCLUDED.age_declined,
                sex = EXCLUDED.sex,
                sex_declined = EXCLUDED.sex_declined,
                preferred_workout_modes = EXCLUDED.preferred_workout_modes,
                food_preference = EXCLUDED.food_preference,
                sessions_per_week = EXCLUDED.sessions_per_week,
                constraints = EXCLUDED.constraints,
                constraints_asked = EXCLUDED.constraints_asked,
                onboarding_complete = EXCLUDED.onboarding_complete,
                awaiting_onboarding_confirm = EXCLUDED.awaiting_onboarding_confirm,
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
                json.dumps(profile.preferred_workout_modes),
                profile.food_preference,
                profile.sessions_per_week,
                json.dumps(profile.constraints),
                profile.constraints_asked,
                profile.onboarding_complete,
                profile.awaiting_onboarding_confirm,
            ),
        )
        c.execute(
            "UPDATE app_users SET name = %s WHERE user_id = %s",
            (profile.name, user_id),
        )
        c.commit()


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


def reset_user(user_id: str) -> None:
    """Wipe one profile's rows (not kb_*). Leaves app_users + blank profile."""
    if not user_exists(user_id):
        raise KeyError(user_id)
    name = get_profile(user_id).name or user_id
    with _conn() as c:
        c.execute("DELETE FROM workout_log WHERE user_id = %s", (user_id,))
        c.execute("DELETE FROM weight_log WHERE user_id = %s", (user_id,))
        c.execute("DELETE FROM week_plans WHERE user_id = %s", (user_id,))
        c.execute(
            "DELETE FROM documents WHERE user_id = %s AND doc_type <> ALL(%s)",
            (user_id, ["kb_exercise", "kb_guide", "kb_template", "kb_science"]),
        )
        # LangGraph checkpointer threads namespaced as user_id:*
        for table in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
            try:
                c.execute(
                    f"DELETE FROM {table} WHERE thread_id LIKE %s",  # noqa: S608
                    (f"{user_id}:%",),
                )
            except Exception:
                pass
        c.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
        c.execute(
            """
            INSERT INTO user_profiles(
                user_id, name, goal, onboarding_complete, awaiting_onboarding_confirm
            ) VALUES (%s, %s, '', FALSE, FALSE)
            """,
            (user_id, name),
        )
        c.commit()

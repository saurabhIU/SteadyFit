"""Long-term memory: user profile + adherence stats (SQLite)."""
import json
import sqlite3
from datetime import date, timedelta

from app.config import settings
from app.graph.state import UserProfile, WeekPlan

SCHEMA = """
CREATE TABLE IF NOT EXISTS workout_log (
    id INTEGER PRIMARY KEY, date TEXT, focus TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS weight_log (
    id INTEGER PRIMARY KEY, date TEXT, kg REAL
);
CREATE TABLE IF NOT EXISTS profile (
    key TEXT PRIMARY KEY, value TEXT
);
"""


def _conn():
    c = sqlite3.connect(settings.profile_db)
    c.executescript(SCHEMA)
    return c


def log_workout(date: str, focus: str, status: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO workout_log(date,focus,status) VALUES (?,?,?)",
            (date, focus, status),
        )


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _weekly_done_counts() -> dict[date, int]:
    """Distinct calendar days with at least one completed workout per ISO week."""
    weekly_days: dict[date, set[str]] = {}
    with _conn() as c:
        rows = c.execute("SELECT date, status FROM workout_log").fetchall()
    for date_str, status in rows:
        if status != "done":
            continue
        try:
            d = date.fromisoformat(str(date_str)[:10])
        except ValueError:
            continue
        ws = _week_start(d)
        weekly_days.setdefault(ws, set()).add(d.isoformat())
    return {ws: len(days) for ws, days in weekly_days.items()}


def _streak_threshold(sessions_per_week: int) -> int:
    """~60% of weekly target, minimum one session — steady, not perfect."""
    return max(1, (sessions_per_week * 3 + 4) // 5)


def get_week_streak(sessions_per_week: int = 3, *, as_of: date | None = None) -> int:
    """Consecutive ISO weeks (through current) meeting the attendance bar."""
    threshold = _streak_threshold(sessions_per_week)
    weekly = _weekly_done_counts()
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


def get_adherence_stats() -> dict:
    profile = get_profile()
    sessions = profile.sessions_per_week or 3
    with _conn() as c:
        rows = c.execute(
            "SELECT status, COUNT(*) FROM workout_log "
            "WHERE date >= date('now','-14 day') GROUP BY status"
        ).fetchall()
    stats = {status: n for status, n in rows}
    done, skipped = stats.get("done", 0), stats.get("skipped", 0)
    total = done + skipped
    return {
        "last14d": stats,
        "adherence_pct": round(100 * done / total) if total else None,
        "drop_off_signal": skipped >= 3,
        "streak_weeks": get_week_streak(sessions),
    }


def _parse_int(raw: str | None) -> int | None:
    if raw is None or raw == "" or raw == "None":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes"}


def get_profile() -> UserProfile:
    """Load profile; migrates legacy keys (injuries, food_preferences, …)."""
    with _conn() as c:
        rows = c.execute("SELECT key, value FROM profile WHERE key != 'week_plan'").fetchall()
    if not rows:
        return UserProfile()
    data = dict(rows)

    # --- migrate legacy fields into the new schema ---
    constraints = json.loads(data.get("constraints", "[]") or "[]")
    if not constraints and data.get("injuries"):
        try:
            constraints = json.loads(data["injuries"])
        except json.JSONDecodeError:
            constraints = []

    modes = json.loads(data.get("preferred_workout_modes", "[]") or "[]")
    if not modes and data.get("workout_preferences"):
        try:
            modes = json.loads(data["workout_preferences"])
        except json.JSONDecodeError:
            modes = []

    food = data.get("food_preference") or None
    if not food and data.get("food_preferences"):
        try:
            prefs = json.loads(data["food_preferences"])
            food = prefs[0] if prefs else None
        except json.JSONDecodeError:
            food = None

    sessions = _parse_int(data.get("sessions_per_week"))

    goal = data.get("goal", "") or ""
    onboarding = _parse_bool(data.get("onboarding_complete"), default=False)
    # Existing seeded profiles (had a real goal + modes) count as complete if flag absent.
    if "onboarding_complete" not in data and goal and goal != "general fitness" and modes:
        onboarding = True
    if goal == "general fitness" and not onboarding:
        goal = ""

    return UserProfile(
        name=data.get("name", "athlete") or "athlete",
        goal=goal,
        age=_parse_int(data.get("age")),
        age_declined=_parse_bool(data.get("age_declined")),
        sex=data.get("sex") or None,
        sex_declined=_parse_bool(data.get("sex_declined")),
        preferred_workout_modes=list(modes),
        food_preference=food,
        sessions_per_week=sessions,
        constraints=list(constraints),
        constraints_asked=_parse_bool(data.get("constraints_asked")),
        onboarding_complete=onboarding,
        awaiting_onboarding_confirm=_parse_bool(data.get("awaiting_onboarding_confirm")),
    )


def save_profile(profile: UserProfile):
    rows = {
        "name": profile.name,
        "goal": profile.goal,
        "age": "" if profile.age is None else str(profile.age),
        "age_declined": str(profile.age_declined),
        "sex": profile.sex or "",
        "sex_declined": str(profile.sex_declined),
        "preferred_workout_modes": json.dumps(profile.preferred_workout_modes),
        "food_preference": profile.food_preference or "",
        "sessions_per_week": (
            "" if profile.sessions_per_week is None else str(profile.sessions_per_week)
        ),
        "constraints": json.dumps(profile.constraints),
        "constraints_asked": str(profile.constraints_asked),
        "onboarding_complete": str(profile.onboarding_complete),
        "awaiting_onboarding_confirm": str(profile.awaiting_onboarding_confirm),
        # Legacy mirrors for older readers
        "injuries": json.dumps(profile.constraints),
        "food_preferences": json.dumps(
            [profile.food_preference] if profile.food_preference else []
        ),
        "workout_preferences": json.dumps(profile.preferred_workout_modes),
    }
    with _conn() as c:
        for key, value in rows.items():
            c.execute(
                "INSERT INTO profile(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )


def get_saved_week_plan() -> WeekPlan | None:
    with _conn() as c:
        row = c.execute("SELECT value FROM profile WHERE key = 'week_plan'").fetchone()
    if not row:
        return None
    try:
        return WeekPlan(**json.loads(row[0]))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def save_week_plan(plan: WeekPlan | dict):
    payload = plan.model_dump() if isinstance(plan, WeekPlan) else plan
    with _conn() as c:
        c.execute(
            "INSERT INTO profile(key, value) VALUES ('week_plan', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (json.dumps(payload),),
        )


def clear_profile_slots():
    """Wipe profile keys (keep week_plan / logs) — used by seed --fresh."""
    keep = {"week_plan"}
    with _conn() as c:
        rows = c.execute("SELECT key FROM profile").fetchall()
        for (key,) in rows:
            if key not in keep:
                c.execute("DELETE FROM profile WHERE key = ?", (key,))

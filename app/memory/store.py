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
    weekly: dict[date, int] = {}
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
        weekly[ws] = weekly.get(ws, 0) + 1
    return weekly


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
            # Current week still in progress — don't break; check prior weeks.
            week -= timedelta(days=7)
        else:
            break
    return streak


def get_adherence_stats() -> dict:
    profile = get_profile()
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
        "streak_weeks": get_week_streak(profile.sessions_per_week),
    }


def get_profile() -> UserProfile:
    with _conn() as c:
        rows = c.execute("SELECT key, value FROM profile WHERE key != 'week_plan'").fetchall()
    if not rows:
        return UserProfile()
    data = dict(rows)
    return UserProfile(
        name=data.get("name", "athlete"),
        goal=data.get("goal", "general fitness"),
        sessions_per_week=int(data.get("sessions_per_week", 3)),
        injuries=json.loads(data.get("injuries", "[]")),
        food_preferences=json.loads(data.get("food_preferences", "[]")),
        workout_preferences=json.loads(data.get("workout_preferences", "[]")),
    )


def save_profile(profile: UserProfile):
    rows = {
        "name": profile.name,
        "goal": profile.goal,
        "sessions_per_week": str(profile.sessions_per_week),
        "injuries": json.dumps(profile.injuries),
        "food_preferences": json.dumps(profile.food_preferences),
        "workout_preferences": json.dumps(profile.workout_preferences),
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

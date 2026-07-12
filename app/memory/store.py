"""Long-term memory: user profile + adherence stats (SQLite)."""
import json
import sqlite3

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


def get_adherence_stats() -> dict:
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

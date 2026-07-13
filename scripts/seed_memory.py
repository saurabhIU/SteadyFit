"""Seed demo profile, week plan, and workout logs for local development.

Run: uv run python scripts/seed_memory.py
"""
from datetime import date, timedelta

from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.memory import store
from app.memory.store import log_workout, save_profile, save_week_plan

PROFILE = UserProfile(
    name="Saurabh",
    goal="lose 8kg by November while keeping strength",
    sessions_per_week=5,
    injuries=["mild lower-back sensitivity"],
    food_preferences=["high-protein", "Indian food", "no pork", "no beef"],
    workout_preferences=["upper push", "lower body", "full body + conditioning"],
)

WEEK_START = (date.today() - timedelta(days=date.today().weekday())).isoformat()
WEEK_PLAN = WeekPlan(
    week_start=WEEK_START,
    days=[
        WorkoutDay(day="Mon", focus="Upper push", duration_min=45),
        WorkoutDay(day="Wed", focus="Lower body", duration_min=50),
        WorkoutDay(day="Fri", focus="Full body + conditioning", duration_min=40),
    ],
    calorie_target=2200,
    protein_target_g=155,
    notes="Default 3-day split — scheduler will adapt around travel and misses.",
)


def main():
    save_profile(PROFILE)
    save_week_plan(WEEK_PLAN)

    with store._conn() as c:
        c.execute("DELETE FROM workout_log")

    today = date.today()
    samples = [
        (today - timedelta(days=10), "Upper push", "done"),
        (today - timedelta(days=8), "Lower body", "skipped"),
        (today - timedelta(days=6), "Conditioning", "skipped"),
        (today - timedelta(days=4), "Upper pull", "skipped"),
        (today - timedelta(days=2), "Lower body", "done"),
    ]
    for day, focus, status in samples:
        log_workout(day.isoformat(), focus, status)

    print(f"Seeded profile for {PROFILE.name}")
    print(f"Seeded week plan starting {WEEK_START}")
    print(f"Logged {len(samples)} workouts (3 skipped in last 14d → drop-off signal)")


if __name__ == "__main__":
    main()

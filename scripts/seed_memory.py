"""Seed demo profile, week plan, and workout logs for local development.

  uv run python scripts/seed_memory.py           # complete profile (skip onboarding)
  uv run python scripts/seed_memory.py --fresh   # empty profile for intake demo
"""
import argparse
from datetime import date, timedelta

from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.memory import store
from app.memory.store import clear_profile_slots, log_workout, save_profile, save_week_plan

PROFILE = UserProfile(
    name="Saurabh",
    goal="lose 8kg by November while keeping strength",
    age=34,
    sex="male",
    preferred_workout_modes=["gym", "walking"],
    food_preference="non-vegetarian",
    sessions_per_week=5,
    constraints=["mild lower-back sensitivity"],
    constraints_asked=True,
    onboarding_complete=True,
    awaiting_onboarding_confirm=False,
)

FRESH_PROFILE = UserProfile(
    name="athlete",
    goal="",
    onboarding_complete=False,
    awaiting_onboarding_confirm=False,
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


def seed_complete():
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

    print(f"Seeded complete profile for {PROFILE.name} (onboarding_complete=True)")
    print(f"Seeded week plan starting {WEEK_START}")
    print(f"Logged {len(samples)} workouts (3 skipped in last 14d → drop-off signal)")


def seed_fresh():
    clear_profile_slots()
    save_profile(FRESH_PROFILE)
    with store._conn() as c:
        c.execute("DELETE FROM workout_log")
        c.execute("DELETE FROM profile WHERE key = 'week_plan'")
    print("Seeded INCOMPLETE profile (onboarding_complete=False) — ready for intake demo")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Seed an incomplete profile so conversational onboarding can be demoed",
    )
    args = parser.parse_args()
    if args.fresh:
        seed_fresh()
    else:
        seed_complete()


if __name__ == "__main__":
    main()

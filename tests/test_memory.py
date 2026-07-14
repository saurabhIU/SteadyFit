"""Tests for long-term memory loading and persistence."""
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.memory import store
from app.memory.context import bootstrap_input, plan_snapshot, week_plan_from_graph


@pytest.fixture
def memory_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_profile.sqlite"
    monkeypatch.setattr(store.settings, "profile_db", str(db_path))
    return db_path


def test_profile_round_trip(memory_db):
    profile = UserProfile(
        name="Sam",
        goal="build muscle",
        sessions_per_week=4,
        constraints=["knee"],
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        onboarding_complete=True,
    )
    store.save_profile(profile)
    loaded = store.get_profile()
    assert loaded.name == "Sam"
    assert loaded.goal == "build muscle"
    assert loaded.constraints == ["knee"]
    assert loaded.injuries == ["knee"]
    assert loaded.food_preference == "vegetarian"
    assert loaded.onboarding_complete is True


def test_fresh_incomplete_profile(memory_db):
    store.save_profile(UserProfile())
    loaded = store.get_profile()
    assert loaded.onboarding_complete is False
    assert loaded.goal == ""
    assert loaded.sessions_per_week is None


def test_week_plan_round_trip(memory_db):
    plan = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Mon", focus="Push", duration_min=40)],
        calorie_target=2000,
        protein_target_g=140,
    )
    store.save_week_plan(plan)
    loaded = store.get_saved_week_plan()
    assert loaded is not None
    assert loaded.week_start == "2026-07-14"
    assert loaded.days[0].focus == "Push"


def test_adherence_stats_detects_drop_off(memory_db):
    store.log_workout("2026-07-01", "Legs", "skipped")
    store.log_workout("2026-07-02", "Push", "skipped")
    store.log_workout("2026-07-03", "Pull", "skipped")
    store.log_workout("2026-07-04", "Legs", "done")
    stats = store.get_adherence_stats()
    assert stats["drop_off_signal"] is True
    assert stats["last14d"]["skipped"] == 3
    assert stats["streak_weeks"] == 0


def test_week_streak_counts_consecutive_weeks(memory_db):
    store.save_profile(
        UserProfile(name="Sam", goal="fit", sessions_per_week=3, onboarding_complete=True)
    )
    as_of = date(2026, 7, 14)  # Monday
    # Threshold is 2 done/week for 3 sessions target.
    for offset in (7, 8, 14, 15, 21, 22):
        store.log_workout(
            (as_of - timedelta(days=offset)).isoformat(),
            "Workout",
            "done",
        )
    assert store.get_week_streak(3, as_of=as_of) == 3


class FakeGraph:
    def __init__(self, values):
        self._values = values

    def get_state(self, _config):
        class Snapshot:
            pass

        snapshot = Snapshot()
        snapshot.values = self._values
        return snapshot


def test_bootstrap_input_uses_sqlite_when_no_checkpoint(memory_db):
    store.save_profile(UserProfile(name="Riley", goal="cut fat"))
    store.save_week_plan(
        WeekPlan(week_start="2026-07-07", days=[WorkoutDay(day="Mon", focus="Run")])
    )
    payload = bootstrap_input(FakeGraph(None), "thread-1")
    assert payload.profile.name == "Riley"
    assert payload.week_plan is not None
    assert payload.week_plan.days[0].focus == "Run"


def test_bootstrap_prefers_checkpoint_week_plan(memory_db):
    store.save_week_plan(
        WeekPlan(week_start="2026-07-07", days=[WorkoutDay(day="Mon", focus="Old")])
    )
    checkpoint_plan = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Tue", focus="New")],
    )
    payload = bootstrap_input(FakeGraph({"week_plan": checkpoint_plan}), "thread-1")
    assert payload.week_plan is not None
    assert payload.week_plan.days[0].focus == "New"


def test_plan_snapshot_returns_serializable_payload(memory_db):
    store.save_profile(UserProfile(name="Alex"))
    store.save_week_plan(
        WeekPlan(week_start="2026-07-14", days=[WorkoutDay(day="Wed", focus="Lower")])
    )
    out = plan_snapshot(FakeGraph(None), "thread-abc")
    assert out["thread_id"] == "thread-abc"
    assert out["profile"]["name"] == "Alex"
    assert out["week_plan"]["days"][0]["focus"] == "Lower"
    assert "adherence" in out
    json.dumps(out)

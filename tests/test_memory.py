"""Tests for long-term memory loading and persistence (Postgres)."""
from __future__ import annotations

import json
import uuid
from datetime import date, timedelta

import pytest

from app.config import settings
from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.memory import store
from app.memory.context import bootstrap_input, plan_snapshot


@pytest.fixture
def uid():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    user_id = f"test-mem-{uuid.uuid4().hex[:8]}"
    store.ensure_user(user_id, "Test")
    yield user_id
    try:
        store.reset_user(user_id)
        with store._conn() as c:
            c.execute("DELETE FROM app_users WHERE user_id = %s", (user_id,))
            c.commit()
    except Exception:
        pass


def test_profile_round_trip(uid):
    profile = UserProfile(
        name="Sam",
        goal="build muscle",
        sessions_per_week=4,
        constraints=["knee"],
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        onboarding_complete=True,
    )
    store.save_profile(uid, profile)
    loaded = store.get_profile(uid)
    assert loaded.name == "Sam"
    assert loaded.goal == "build muscle"
    assert loaded.constraints == ["knee"]
    assert loaded.injuries == ["knee"]
    assert loaded.food_preference == "vegetarian"
    assert loaded.onboarding_complete is True


def test_fresh_incomplete_profile(uid):
    store.save_profile(uid, UserProfile(name="Blank"))
    loaded = store.get_profile(uid)
    assert loaded.onboarding_complete is False
    assert loaded.goal == ""
    assert loaded.sessions_per_week is None


def test_week_plan_round_trip(uid):
    plan = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Mon", focus="Push", duration_min=40)],
        calorie_target=2000,
        protein_target_g=140,
    )
    store.save_week_plan(uid, plan)
    loaded = store.get_saved_week_plan(uid)
    assert loaded is not None
    assert loaded.week_start == "2026-07-14"
    assert loaded.days[0].focus == "Push"


def test_adherence_stats_detects_drop_off(uid):
    today = date.today()
    for i, status in enumerate(("skipped", "skipped", "skipped", "done")):
        store.log_workout(
            uid,
            (today - timedelta(days=3 - i)).isoformat(),
            "Workout",
            status,
        )
    stats = store.get_adherence_stats(uid)
    assert stats["drop_off_signal"] is True
    assert stats["last14d"]["skipped"] == 3
    assert stats["streak_weeks"] == 0


def test_week_streak_counts_consecutive_weeks(uid):
    store.save_profile(
        uid,
        UserProfile(name="Sam", goal="fit", sessions_per_week=3, onboarding_complete=True),
    )
    as_of = date(2026, 7, 14)  # Monday
    for offset in (7, 8, 14, 15, 21, 22):
        store.log_workout(
            uid,
            (as_of - timedelta(days=offset)).isoformat(),
            "Workout",
            "done",
        )
    assert store.get_week_streak(uid, 3, as_of=as_of) == 3


class FakeGraph:
    def __init__(self, values):
        self._values = values

    def get_state(self, _config):
        class Snapshot:
            pass

        snapshot = Snapshot()
        snapshot.values = self._values
        return snapshot


def test_bootstrap_input_uses_store_when_no_checkpoint(uid):
    store.save_profile(uid, UserProfile(name="Riley", goal="cut fat"))
    store.save_week_plan(
        uid,
        WeekPlan(week_start="2026-07-07", days=[WorkoutDay(day="Mon", focus="Run")]),
    )
    payload = bootstrap_input(FakeGraph(None), f"{uid}:thread-1", user_id=uid)
    assert payload.profile.name == "Riley"
    assert payload.week_plan is not None
    assert payload.week_plan.days[0].focus == "Run"
    assert payload.user_id == uid


def test_bootstrap_prefers_checkpoint_week_plan(uid):
    store.save_week_plan(
        uid,
        WeekPlan(week_start="2026-07-07", days=[WorkoutDay(day="Mon", focus="Old")]),
    )
    checkpoint_plan = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Tue", focus="New")],
    )
    payload = bootstrap_input(
        FakeGraph({"week_plan": checkpoint_plan}),
        f"{uid}:thread-1",
        user_id=uid,
    )
    assert payload.week_plan is not None
    assert payload.week_plan.days[0].focus == "New"


def test_plan_snapshot_returns_serializable_payload(uid):
    store.save_profile(uid, UserProfile(name="Alex"))
    store.save_week_plan(
        uid,
        WeekPlan(week_start="2026-07-14", days=[WorkoutDay(day="Wed", focus="Lower")]),
    )
    out = plan_snapshot(FakeGraph(None), f"{uid}:thread-abc", uid)
    assert out["thread_id"] == f"{uid}:thread-abc"
    assert out["user_id"] == uid
    assert out["profile"]["name"] == "Alex"
    assert out["week_plan"]["days"][0]["focus"] == "Lower"
    assert "adherence" in out
    json.dumps(out)

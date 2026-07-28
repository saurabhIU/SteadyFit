"""Evals for quick-10 Done logging cases + modality defaults."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from app.config import settings
from app.graph.micro_workout import (
    EXTRA_CHIP,
    QUICK_FOCUS,
    QUICK_SOURCE,
    REPLACE_CHIP,
    SOFT_PREF_LINE,
    build_ten_minute_reply,
    handle_quick_10_choice,
    handle_quick_10_done,
    looks_like_quick_10_extra,
    looks_like_quick_10_replace,
    resolve_today_plan_context,
)
from app.graph.plan_utils import current_week_monday, date_for_weekday
from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.memory import store


@pytest.fixture
def uid():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    user_id = f"test-q10-{uuid.uuid4().hex[:8]}"
    store.ensure_user(user_id, "Quick10")
    yield user_id
    try:
        store.reset_user(user_id)
        with store._conn() as c:
            c.execute("DELETE FROM app_users WHERE user_id = %s", (user_id,))
            c.commit()
    except Exception:
        pass


def _plan_for_today(
    *,
    today: date,
    status: str,
    include_today: bool = True,
) -> WeekPlan:
    monday = current_week_monday(today)
    days: list[WorkoutDay] = []
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, name in enumerate(names):
        d = monday + timedelta(days=i)
        if d == today and not include_today:
            continue
        if d == today:
            days.append(
                WorkoutDay(day=name, focus="Today strength", duration_min=40, status=status)  # type: ignore[arg-type]
            )
        elif i in (0, 2, 4):  # Mon Wed Fri placeholders
            days.append(
                WorkoutDay(day=name, focus=f"{name} work", duration_min=40, status="planned")
            )
    return WeekPlan(week_start=monday.isoformat(), days=days, calorie_target=2100, protein_target_g=140)


def test_choice_phrase_matching():
    """Free-text must hit dedicated replace/extra handlers — not the LLM."""
    assert looks_like_quick_10_extra("log it separately")
    assert looks_like_quick_10_extra("Log it separately")
    assert looks_like_quick_10_extra("log separately")
    assert looks_like_quick_10_extra("keep both")
    assert looks_like_quick_10_extra("in addition to current workout")
    assert not looks_like_quick_10_extra("I have 10 minutes")

    assert looks_like_quick_10_replace("Count as today's session")
    assert looks_like_quick_10_replace("count this as today's session")
    assert looks_like_quick_10_replace("Replace today's session")
    assert not looks_like_quick_10_replace("log it separately")


def test_resolve_cases_same_week_start_source():
    today = date(2026, 7, 29)  # Wednesday
    monday = current_week_monday(today)
    assert monday == date(2026, 7, 27)
    assert date_for_weekday(monday.isoformat(), "Wednesday") == today

    assert resolve_today_plan_context(None, as_of=today).case == "no_plan"

    rest_plan = _plan_for_today(today=today, status="planned", include_today=False)
    assert resolve_today_plan_context(rest_plan, as_of=today).case == "rest"

    pending = _plan_for_today(today=today, status="planned")
    assert resolve_today_plan_context(pending, as_of=today).case == "planned_pending"

    done = _plan_for_today(today=today, status="done")
    assert resolve_today_plan_context(done, as_of=today).case == "planned_done"


def test_bodyweight_default_and_gym_preference():
    bare = UserProfile(name="A", onboarding_complete=True)
    reply = build_ten_minute_reply(bare).lower()
    assert "bodyweight" in reply or "living room" in reply

    gym = UserProfile(
        name="B",
        preferred_workout_modes=["gym"],
        onboarding_complete=True,
    )
    gym_reply = build_ten_minute_reply(gym).lower()
    assert "goblet" in gym_reply or "farmer" in gym_reply or "rdl" in gym_reply


def test_no_plan_logs_without_prompt(uid):
    today = date.today()
    profile = UserProfile(name="New", onboarding_complete=False)
    result = handle_quick_10_done(
        user_id=uid, profile=profile, week_plan=None, as_of=today
    )
    assert result.awaiting_choice is False
    assert result.quick_replies == []
    assert "Logged your 10-minute session" in result.reply
    assert SOFT_PREF_LINE in result.reply  # no modality yet
    rows = store.get_workouts_on(uid, today.isoformat())
    assert any(r["source"] == QUICK_SOURCE and r["focus"] == QUICK_FOCUS for r in rows)


def test_rest_day_bonus_no_prompt(uid):
    today = date.today()
    plan = _plan_for_today(today=today, status="planned", include_today=False)
    store.save_week_plan(uid, plan)
    profile = UserProfile(
        name="Rest",
        preferred_workout_modes=["home"],
        onboarding_complete=True,
    )
    result = handle_quick_10_done(
        user_id=uid, profile=profile, week_plan=plan, as_of=today
    )
    assert result.awaiting_choice is False
    assert result.quick_replies == []
    assert SOFT_PREF_LINE not in result.reply
    loaded = store.get_saved_week_plan(uid)
    assert loaded is not None
    # No day should flip to done
    for d in loaded.days:
        day_date = date_for_weekday(loaded.week_start, d.day)
        if day_date == today:
            pytest.fail("rest fixture should not include today")


def test_pending_prompt_and_both_chips(uid):
    today = date.today()
    plan = _plan_for_today(today=today, status="planned")
    store.save_week_plan(uid, plan)
    profile = UserProfile(
        name="Busy",
        preferred_workout_modes=["gym"],
        onboarding_complete=True,
    )

    done = handle_quick_10_done(
        user_id=uid, profile=profile, week_plan=plan, as_of=today
    )
    assert done.awaiting_choice is True
    assert REPLACE_CHIP in done.quick_replies
    assert EXTRA_CHIP in done.quick_replies
    assert "Count this as today's session" in done.reply
    assert any(r["source"] == QUICK_SOURCE for r in store.get_workouts_on(uid, today.isoformat()))

    # Extra keeps day planned; quick log stays visible via workout_log
    extra = handle_quick_10_choice(
        user_id=uid,
        profile=profile,
        week_plan=plan,
        choice="extra",
        as_of=today,
    )
    assert extra.awaiting_choice is False
    assert "bonus" in extra.reply.lower()
    loaded = store.get_saved_week_plan(uid)
    assert loaded is not None
    today_day = next(
        d
        for d in loaded.days
        if date_for_weekday(loaded.week_start, d.day) == today
    )
    assert today_day.status == "planned"
    week_logs = store.get_week_workout_logs(uid, loaded.week_start)
    assert any(r["source"] == QUICK_SOURCE for r in week_logs)

    # Fresh pending plan for replace path
    plan2 = _plan_for_today(today=today, status="planned")
    store.save_week_plan(uid, plan2)
    handle_quick_10_done(user_id=uid, profile=profile, week_plan=plan2, as_of=today)
    replaced = handle_quick_10_choice(
        user_id=uid,
        profile=profile,
        week_plan=plan2,
        choice="replace",
        as_of=today,
    )
    assert replaced.week_plan is not None
    today_day2 = next(
        d
        for d in replaced.week_plan.days
        if date_for_weekday(replaced.week_plan.week_start, d.day) == today
    )
    assert today_day2.status == "done"
    persisted = store.get_saved_week_plan(uid)
    assert persisted is not None
    today_persisted = next(
        d
        for d in persisted.days
        if date_for_weekday(persisted.week_start, d.day) == today
    )
    assert today_persisted.status == "done"


def test_already_done_bonus_no_prompt(uid):
    today = date.today()
    plan = _plan_for_today(today=today, status="done")
    store.save_week_plan(uid, plan)
    profile = UserProfile(
        name="Done",
        preferred_workout_modes=["walking"],
        onboarding_complete=True,
    )
    result = handle_quick_10_done(
        user_id=uid, profile=profile, week_plan=plan, as_of=today
    )
    assert result.awaiting_choice is False
    assert result.quick_replies == []
    rows = store.get_workouts_on(uid, today.isoformat())
    assert any(r["source"] == QUICK_SOURCE for r in rows)

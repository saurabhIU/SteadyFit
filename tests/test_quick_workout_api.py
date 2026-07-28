"""API-level evals: Done via /api/quick-workout/complete never hits intake."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.graph.micro_workout import (
    EXTRA_CHIP,
    QUICK_SOURCE,
    REPLACE_CHIP,
)
from app.graph.plan_utils import current_week_monday, date_for_weekday
from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.main import app
from app.memory import store


@pytest.fixture
def client():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mid_intake_user():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    user_id = f"test-q10-api-{uuid.uuid4().hex[:8]}"
    store.ensure_user(user_id, "Mid Intake")
    store.save_profile(
        user_id,
        UserProfile(
            name="Mid Intake",
            goal="",  # pending intake question
            onboarding_complete=False,
            awaiting_onboarding_confirm=False,
        ),
    )
    yield user_id
    try:
        store.reset_user(user_id)
        with store._conn() as c:
            c.execute("DELETE FROM app_users WHERE user_id = %s", (user_id,))
            c.commit()
    except Exception:
        pass


def _plan_for_today(*, today: date, status: str, include_today: bool = True) -> WeekPlan:
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
        elif i in (0, 2, 4):
            days.append(
                WorkoutDay(day=name, focus=f"{name} work", duration_min=40, status="planned")
            )
    return WeekPlan(
        week_start=monday.isoformat(),
        days=days,
        calorie_target=2100,
        protein_target_g=140,
    )


def test_done_mid_onboarding_does_not_corrupt_intake(client, mid_intake_user):
    """Bug reproduction: Done must not become the goal answer."""
    uid = mid_intake_user
    headers = {"X-User-Id": uid}

    # Ask the pending goal question via normal chat (intake).
    r = client.post(
        "/api/chat",
        headers=headers,
        json={"message": "hi", "thread_id": "q10-mid"},
    )
    assert r.status_code == 200
    before = store.get_profile(uid)
    assert before.onboarding_complete is False
    assert (before.goal or "").strip() == ""

    # Structured Done — must NOT go through chat/intake.
    done = client.post(
        "/api/quick-workout/complete",
        headers=headers,
        json={"action": "done", "thread_id": "q10-mid"},
    )
    assert done.status_code == 200
    payload = done.json()
    assert payload["scope"] == "quick_workout_action"
    assert "Logged your 10-minute session" in payload["reply"]
    assert payload["case"] == "no_plan"
    assert payload["logged"] is True

    today = date.today().isoformat()
    rows = store.get_workouts_on(uid, today)
    assert any(r["source"] == QUICK_SOURCE for r in rows)

    after = store.get_profile(uid)
    assert after.onboarding_complete is False
    assert (after.goal or "").strip() == ""
    assert after.goal != "done"
    assert (after.sessions_per_week is None) or (before.sessions_per_week == after.sessions_per_week)


def test_api_rest_and_pending_and_already_done(client, mid_intake_user):
    uid = mid_intake_user
    headers = {"X-User-Id": uid}
    today = date.today()

    # Rest day
    store.save_week_plan(uid, _plan_for_today(today=today, status="planned", include_today=False))
    store.save_profile(
        uid,
        UserProfile(
            name="Rest",
            goal="lose fat",
            preferred_workout_modes=["home"],
            sessions_per_week=3,
            food_preference="vegetarian",
            onboarding_complete=True,
            constraints_asked=True,
        ),
    )
    rest = client.post(
        "/api/quick-workout/complete",
        headers=headers,
        json={"action": "done", "thread_id": "q10-rest"},
    ).json()
    assert rest["case"] == "rest"
    assert rest["awaiting_choice"] is False
    assert rest["quick_replies"] == []
    assert "Logged your 10-minute session" in rest["reply"]

    # Planned pending → chips
    store.save_week_plan(uid, _plan_for_today(today=today, status="planned"))
    pending = client.post(
        "/api/quick-workout/complete",
        headers=headers,
        json={"action": "done", "thread_id": "q10-pending"},
    ).json()
    assert pending["case"] == "planned_pending"
    assert pending["awaiting_choice"] is True
    assert REPLACE_CHIP in pending["quick_replies"]
    assert EXTRA_CHIP in pending["quick_replies"]

    extra = client.post(
        "/api/quick-workout/complete",
        headers=headers,
        json={"action": "extra", "thread_id": "q10-pending"},
    ).json()
    assert "bonus" in extra["reply"].lower() or "extra" in extra["reply"].lower()
    plan = store.get_saved_week_plan(uid)
    assert plan is not None
    for d in plan.days:
        if date_for_weekday(plan.week_start, d.day) == today:
            assert d.status == "planned"

    # Replace path
    store.save_week_plan(uid, _plan_for_today(today=today, status="planned"))
    client.post(
        "/api/quick-workout/complete",
        headers=headers,
        json={"action": "done", "thread_id": "q10-replace"},
    )
    replaced = client.post(
        "/api/quick-workout/complete",
        headers=headers,
        json={"action": "replace", "thread_id": "q10-replace"},
    ).json()
    plan2 = store.get_saved_week_plan(uid)
    assert plan2 is not None
    for d in plan2.days:
        if date_for_weekday(plan2.week_start, d.day) == today:
            assert d.status == "done"
    assert "marked done" in replaced["reply"].lower() or "today" in replaced["reply"].lower()

    # Already done → bonus, no prompt
    store.save_week_plan(uid, _plan_for_today(today=today, status="done"))
    again = client.post(
        "/api/quick-workout/complete",
        headers=headers,
        json={"action": "done", "thread_id": "q10-again"},
    ).json()
    assert again["case"] == "planned_done"
    assert again["awaiting_choice"] is False
    assert again["quick_replies"] == []

"""Upload-hint: one soft invite after onboarding → first_plan handoff."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from langchain_core.messages import HumanMessage

from app.config import settings
from app.graph.agents.intake import UPLOAD_HINT, _handoff_first_plan, intake_node
from app.graph.state import CoachingTeamState, UserProfile, WeekPlan, WorkoutDay
from app.memory import store


def _filled_profile(**kwargs) -> UserProfile:
    base = dict(
        name="Hint Tester",
        goal="lose fat",
        sessions_per_week=3,
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        constraints_asked=True,
        onboarding_complete=False,
        awaiting_onboarding_confirm=True,
        shown_upload_hint=False,
        # Skip diet gate so confirm → first_plan in one turn.
        weight_kg=75.0,
        target_weight_declined=True,
        height_cm=175.0,
        age=34,
        sex="male",
        activity_level="moderate",
    )
    base.update(kwargs)
    return UserProfile(**base)


def test_upload_hint_appended_on_first_handoff():
    profile = _filled_profile()
    state = CoachingTeamState(user_id="hint-u1", profile=profile)
    with patch("app.graph.agents.intake.user_has_personal_docs", return_value=False):
        with patch("app.graph.agents.intake.save_profile"):
            out = _handoff_first_plan(
                profile,
                state,
                preamble=(
                    "Awesome — I'll draft your first week from that profile. "
                    "You'll see an approval card below before anything sticks."
                ),
            )
    assert out["intent"] == "first_plan"
    reply = out["messages"][0]["content"]
    assert UPLOAD_HINT in reply
    assert "Update tab" in reply
    assert "Awesome — I'll draft" in reply
    assert out["profile"].shown_upload_hint is True
    assert out["proposals"].get("offer_upload") is True


def test_upload_hint_not_repeated():
    profile = _filled_profile(shown_upload_hint=True)
    state = CoachingTeamState(user_id="hint-u2", profile=profile)
    with patch("app.graph.agents.intake.user_has_personal_docs", return_value=False):
        with patch("app.graph.agents.intake.save_profile"):
            out = _handoff_first_plan(profile, state, preamble="Drafting now.")
    assert UPLOAD_HINT not in out["messages"][0]["content"]
    assert out["intent"] == "first_plan"


def test_upload_hint_skipped_when_personal_docs_exist():
    profile = _filled_profile()
    state = CoachingTeamState(user_id="hint-u3", profile=profile)
    with patch("app.graph.agents.intake.user_has_personal_docs", return_value=True):
        with patch("app.graph.agents.intake.save_profile"):
            out = _handoff_first_plan(profile, state, preamble="Drafting now.")
    assert UPLOAD_HINT not in out["messages"][0]["content"]
    assert out["profile"].shown_upload_hint is True
    assert out["intent"] == "first_plan"


@pytest.fixture
def uid():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    # Ensure column exists for local/dev DBs that predate the migration.
    with store._conn() as c:
        c.execute(
            """
            ALTER TABLE user_profiles
              ADD COLUMN IF NOT EXISTS shown_upload_hint BOOLEAN NOT NULL DEFAULT FALSE
            """
        )
        c.commit()
    user_id = f"test-hint-{uuid.uuid4().hex[:8]}"
    store.ensure_user(user_id, "Hint DB")
    yield user_id
    try:
        store.reset_user(user_id)
        with store._conn() as c:
            c.execute("DELETE FROM app_users WHERE user_id = %s", (user_id,))
            c.commit()
    except Exception:
        pass


def test_confirm_handoff_includes_hint_and_sets_flag(uid):
    profile = _filled_profile()
    store.save_profile(uid, profile)
    state = CoachingTeamState(
        user_id=uid,
        profile=profile,
        messages=[HumanMessage(content="Yes, looks good")],
    )
    with patch("app.graph.agents.intake.user_has_personal_docs", return_value=False):
        with patch("app.graph.agents.intake.get_saved_week_plan", return_value=None):
            out = intake_node(state)

    assert out["intent"] == "first_plan"
    reply = out["messages"][0]["content"]
    assert UPLOAD_HINT in reply
    saved = store.get_profile(uid)
    assert saved.shown_upload_hint is True
    assert saved.onboarding_complete is True

    # Second handoff must not repeat
    profile2 = store.get_profile(uid)
    state2 = CoachingTeamState(user_id=uid, profile=profile2)
    with patch("app.graph.agents.intake.user_has_personal_docs", return_value=False):
        out2 = _handoff_first_plan(profile2, state2, preamble="Another draft.")
    assert UPLOAD_HINT not in out2["messages"][0]["content"]


def test_second_plan_path_no_hint(uid):
    """Later plan-changing conversation: flag already set → no hint."""
    store.save_profile(
        uid,
        _filled_profile(
            onboarding_complete=True,
            awaiting_onboarding_confirm=False,
            shown_upload_hint=True,
        ),
    )
    plan = WeekPlan(
        week_start="2026-07-27",
        days=[WorkoutDay(day="Monday", focus="Full", duration_min=40)],
    )
    store.save_week_plan(uid, plan)
    profile = store.get_profile(uid)
    out = _handoff_first_plan(
        profile,
        CoachingTeamState(user_id=uid, profile=profile),
        preamble="I've adjusted this week.",
    )
    assert UPLOAD_HINT not in out["messages"][0]["content"]

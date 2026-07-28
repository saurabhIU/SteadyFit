"""Legacy post-handoff upload hint retired — see test_upload_offer.py."""

from __future__ import annotations

from unittest.mock import patch

from app.graph.agents.intake import _handoff_first_plan
from app.graph.state import CoachingTeamState, UserProfile


def test_retired_handoff_does_not_append_update_tab_hint():
    profile = UserProfile(
        name="Legacy",
        goal="lose fat",
        sessions_per_week=3,
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        onboarding_complete=True,
        shown_upload_hint=False,
        weight_kg=75,
        height_cm=175,
        age=34,
        sex="male",
        activity_level="moderate",
        target_weight_declined=True,
    )
    with patch("app.graph.agents.intake.save_profile"):
        out = _handoff_first_plan(
            profile,
            CoachingTeamState(user_id="legacy", profile=profile),
            preamble="Awesome — drafting your first week.",
        )
    assert "Update tab" not in out["messages"][0]["content"]
    assert out.get("proposals", {}).get("offer_upload") is None

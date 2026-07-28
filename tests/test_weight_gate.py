"""Hard gate: weight question before first WeekPlan (no plan in the same turn)."""
from app.chat_pipeline import should_skip_scope_gate
from app.graph.agents.intake import intake_node
from app.graph.build import route_from_intake
from app.graph.state import CoachingTeamState, UserProfile, WeekPlan, WorkoutDay
from app.graph.weight_gate import (
    WEIGHT_QUESTION,
    looks_like_weight_decline,
    needs_weight_before_first_plan,
    weight_question_payload,
)


def _fresh_profile(**kwargs) -> UserProfile:
    base = dict(
        name="Try",
        goal="lose fat",
        sessions_per_week=3,
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        constraints_asked=True,
        onboarding_complete=True,
        weight_kg=None,
        weight_declined=False,
        awaiting_weight_for_first_plan=False,
    )
    base.update(kwargs)
    return UserProfile(**base)


def test_needs_weight_only_for_first_plan_without_weight():
    assert needs_weight_before_first_plan(_fresh_profile()) is True
    assert needs_weight_before_first_plan(_fresh_profile(weight_kg=75)) is False
    assert needs_weight_before_first_plan(_fresh_profile(weight_declined=True)) is False
    prior = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Mon", focus="Full body", duration_min=40)],
    )
    assert needs_weight_before_first_plan(_fresh_profile(), saved_plan=prior) is False


def test_weight_question_payload_clears_plan_flags():
    payload = weight_question_payload(_fresh_profile())
    assert payload["intent"] == "intake"
    assert payload["proposals"]["plan_changed"] is False
    assert "proposed_week_plan" not in payload["proposals"]
    assert payload["profile"].awaiting_weight_for_first_plan is True
    assert WEIGHT_QUESTION in payload["messages"][0]["content"]


def test_intake_ask_weight_only_does_not_handoff_plan():
    from unittest.mock import patch

    state = CoachingTeamState(
        user_id="eval-weight-gate",
        profile=_fresh_profile(awaiting_weight_for_first_plan=True),
        messages=[{"role": "user", "content": "Please draft my first week plan."}],
        proposals={"ask_weight_only": True},
    )
    with patch("app.graph.agents.intake.save_profile"):
        out = intake_node(state)
    assert out["intent"] == "intake"
    assert out["proposals"].get("plan_changed") is False
    assert "proposed_week_plan" not in out.get("proposals", {})
    assert route_from_intake(
        CoachingTeamState(intent=out["intent"], proposals=out["proposals"])
    ) == "end"
    assert "weight" in out["messages"][0]["content"].lower()


def test_intake_weight_answer_advances_to_target_weight():
    from unittest.mock import patch

    from app.graph.intake import ProfileExtraction

    state = CoachingTeamState(
        user_id="eval-weight-gate",
        profile=_fresh_profile(awaiting_weight_for_first_plan=True),
        messages=[{"role": "user", "content": "75kg"}],
        proposals={"ask_weight_only": True},
    )
    with (
        patch(
            "app.graph.agents.intake.extract_profile_facts",
            return_value=ProfileExtraction(),
        ),
        patch("app.graph.agents.intake.save_profile"),
    ):
        out = intake_node(state)
    assert out["intent"] == "intake"
    assert out["profile"].weight_kg == 75.0
    assert out["profile"].awaiting_weight_for_first_plan is False
    assert out["proposals"].get("ask_diet_slot") == "target_weight"
    assert "target weight" in out["messages"][0]["content"].lower()
    assert route_from_intake(
        CoachingTeamState(intent=out["intent"], proposals=out["proposals"])
    ) == "end"


def test_intake_decline_advances_to_target_weight():
    from unittest.mock import patch

    from app.graph.intake import ProfileExtraction

    assert looks_like_weight_decline("prefer not to say")
    state = CoachingTeamState(
        user_id="eval-weight-gate",
        profile=_fresh_profile(awaiting_weight_for_first_plan=True),
        messages=[{"role": "user", "content": "prefer not to say"}],
        proposals={"ask_weight_only": True},
    )
    with (
        patch(
            "app.graph.agents.intake.extract_profile_facts",
            return_value=ProfileExtraction(weight_declined=True),
        ),
        patch("app.graph.agents.intake.save_profile"),
    ):
        out = intake_node(state)
    assert out["intent"] == "intake"
    assert out["profile"].weight_declined is True
    assert out["proposals"].get("ask_diet_slot") == "target_weight"
    assert route_from_intake(
        CoachingTeamState(intent=out["intent"], proposals=out["proposals"])
    ) == "end"


def test_awaiting_weight_skips_scope_gate():
    profile = _fresh_profile(awaiting_weight_for_first_plan=True)
    assert should_skip_scope_gate(profile=profile, pending_approval=None) is True


def test_weight_already_elsewhere_gets_ack_not_verbatim_repeat():
    from unittest.mock import patch

    from app.graph.intake import ProfileExtraction
    from app.graph.weight_gate import WEIGHT_ACK_REASK, WEIGHT_QUESTION

    state = CoachingTeamState(
        user_id="eval-weight-ack",
        profile=_fresh_profile(awaiting_weight_for_first_plan=True),
        messages=[{
            "role": "user",
            "content": "I uploaded my document, you should know my weight",
        }],
        proposals={"ask_weight_only": True},
    )
    with (
        patch(
            "app.graph.agents.intake.extract_profile_facts",
            return_value=ProfileExtraction(),
        ),
        patch("app.graph.agents.intake.save_profile"),
    ):
        out = intake_node(state)
    reply = out["messages"][0]["content"]
    assert reply == WEIGHT_ACK_REASK
    assert reply != WEIGHT_QUESTION
    assert "tell me directly" in reply.lower()
    assert out["intent"] == "intake"
    assert out["profile"].awaiting_weight_for_first_plan is True
    assert out["profile"].weight_kg is None


def test_weight_number_unaffected_by_elsewhere_heuristic():
    from unittest.mock import patch

    from app.graph.intake import ProfileExtraction
    from app.graph.weight_gate import WEIGHT_ACK_REASK

    state = CoachingTeamState(
        user_id="eval-weight-num",
        profile=_fresh_profile(awaiting_weight_for_first_plan=True),
        messages=[{"role": "user", "content": "75 kg"}],
        proposals={"ask_weight_only": True},
    )
    with (
        patch(
            "app.graph.agents.intake.extract_profile_facts",
            return_value=ProfileExtraction(),
        ),
        patch("app.graph.agents.intake.save_profile"),
    ):
        out = intake_node(state)
    assert out["profile"].weight_kg == 75.0
    assert WEIGHT_ACK_REASK not in out["messages"][0]["content"]
    assert out["proposals"].get("ask_diet_slot") == "target_weight"


def test_weight_decline_unaffected_by_elsewhere_heuristic():
    from unittest.mock import patch

    from app.graph.intake import ProfileExtraction
    from app.graph.weight_gate import WEIGHT_ACK_REASK

    state = CoachingTeamState(
        user_id="eval-weight-decline",
        profile=_fresh_profile(awaiting_weight_for_first_plan=True),
        messages=[{"role": "user", "content": "prefer not to say"}],
        proposals={"ask_weight_only": True},
    )
    with (
        patch(
            "app.graph.agents.intake.extract_profile_facts",
            return_value=ProfileExtraction(weight_declined=True),
        ),
        patch("app.graph.agents.intake.save_profile"),
    ):
        out = intake_node(state)
    assert out["profile"].weight_declined is True
    assert WEIGHT_ACK_REASK not in out["messages"][0]["content"]
    assert out["proposals"].get("ask_diet_slot") == "target_weight"

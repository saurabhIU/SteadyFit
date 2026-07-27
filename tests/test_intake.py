"""Unit tests for onboarding intake helpers (no live LLM)."""
from unittest.mock import patch

from app.graph.agents.intake import intake_node
from app.graph.intake import (
    IntakePrompt,
    ProfileExtraction,
    apply_extraction,
    build_question,
    extract_profile_facts,
    needs_intake,
    next_intake_question,
    parse_chip_answer,
    required_slots_filled,
    slot_filled,
)
from app.graph.state import CoachingTeamState, UserProfile
from langchain_core.messages import AIMessage, HumanMessage


def test_empty_profile_needs_intake():
    p = UserProfile()
    assert needs_intake(p)
    assert not required_slots_filled(p)
    q = next_intake_question(p)
    assert q is not None
    assert q.slot == "goal"


def test_apply_multi_slot_extraction():
    p = UserProfile()
    ext = ProfileExtraction(
        goal="lose fat",
        age=34,
        sex="male",
        preferred_workout_modes=["walking", "gym"],
        sessions_per_week=3,
        food_preference="vegetarian",
    )
    updated = apply_extraction(p, ext)
    assert updated.goal == "lose fat"
    assert updated.age == 34
    assert "gym" in updated.preferred_workout_modes
    assert required_slots_filled(updated)


def test_age_declined_counts_as_filled():
    p = UserProfile(age_declined=True)
    assert slot_filled(p, "age")
    assert not slot_filled(p, "goal")


def test_build_question_has_chips_for_modes_and_food():
    p = UserProfile(goal="get stronger", sessions_per_week=3)
    modes = build_question("preferred_workout_modes", p)
    assert isinstance(modes, IntakePrompt)
    assert "gym" in modes.quick_replies
    food = build_question("food_preference", p)
    assert "vegan" in food.quick_replies


def test_complete_profile_skips_intake():
    p = UserProfile(
        goal="lose fat",
        sessions_per_week=4,
        preferred_workout_modes=["gym"],
        food_preference="vegan",
        onboarding_complete=True,
    )
    assert not needs_intake(p)


def test_parse_chip_sessions_bare_numeral():
    ext = parse_chip_answer("4", "sessions_per_week")
    assert ext is not None
    assert ext.sessions_per_week == 4
    assert ext.age is None


def test_parse_chip_does_not_steal_sessions_as_age():
    # Without pending slot, chip parser abstains (LLM path would be ambiguous).
    assert parse_chip_answer("4", None) is None
    # With sessions pending, never maps to age.
    ext = parse_chip_answer("4", "sessions_per_week")
    assert ext is not None and ext.age is None and ext.sessions_per_week == 4


def test_parse_chip_food_mode_sex_constraints():
    assert parse_chip_answer("vegetarian", "food_preference").food_preference == "vegetarian"
    assert parse_chip_answer("gym", "preferred_workout_modes").preferred_workout_modes == ["gym"]
    assert parse_chip_answer("male", "sex").sex == "male"
    assert parse_chip_answer("Prefer not to say", "age").age_declined is True
    assert parse_chip_answer("None", "constraints").constraints_none is True


def test_extract_chip_bypasses_llm():
    with patch("app.graph.intake.get_llm") as mock_llm:
        ext = extract_profile_facts("4", pending_slot="sessions_per_week")
        assert ext.sessions_per_week == 4
        mock_llm.assert_not_called()


def test_intake_node_bare_sessions_chip_advances():
    state = CoachingTeamState(
        user_id="chip-sessions",
        profile=UserProfile(
            name="Chip",
            goal="lose fat",
            sessions_per_week=None,
            preferred_workout_modes=[],
            food_preference=None,
            onboarding_complete=False,
        ),
        messages=[
            HumanMessage(content="I want to lose fat"),
            AIMessage(
                content=(
                    "Got it — aiming for lose fat. How many training sessions per week "
                    "feel realistic for your schedule?"
                )
            ),
            HumanMessage(content="4"),
        ],
    )
    with patch("app.graph.agents.intake.save_profile"):
        out = intake_node(state)
    assert out["profile"].sessions_per_week == 4
    reply = out["messages"][0]["content"].lower()
    assert "sessions per week" not in reply
    assert "move" in reply or "gym" in reply or "walking" in reply
    assert next_intake_question(out["profile"]).slot == "preferred_workout_modes"


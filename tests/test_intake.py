"""Unit tests for onboarding intake helpers (no live LLM)."""
from app.graph.intake import (
    IntakePrompt,
    ProfileExtraction,
    apply_extraction,
    build_question,
    needs_intake,
    next_intake_question,
    required_slots_filled,
    slot_filled,
)
from app.graph.state import UserProfile


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

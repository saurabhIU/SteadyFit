"""Unit tests for diet-plan builder + preference safety."""
from app.graph.diet_plan import (
    build_diet_week,
    diet_plan_contains_nonveg,
    diet_plan_violates_preference,
    wants_indian_cuisine,
)
from app.graph.diet_gate import parse_activity_level, parse_height_cm_from_message
from app.graph.state import UserProfile


def test_vegetarian_week_has_no_flesh():
    profile = UserProfile(food_preference="vegetarian")
    meals = build_diet_week(profile, week_start="2026-07-20")
    assert len(meals) >= 21  # 7 days × 3 meals (+ snacks)
    assert not diet_plan_contains_nonveg(meals)
    assert diet_plan_violates_preference(meals, "vegetarian") is None


def test_vegan_week_no_dairy_eggs():
    import re

    profile = UserProfile(food_preference="vegan")
    meals = build_diet_week(profile, week_start="2026-07-20")
    assert diet_plan_violates_preference(meals, "vegan") is None
    blob = " ".join(m["food_description"].lower() for m in meals)
    assert "chicken" not in blob
    assert not re.search(r"\beggs?\b", blob)


def test_default_cuisine_is_neutral():
    profile = UserProfile(food_preference="no-preference")
    assert not wants_indian_cuisine(profile)
    meals = build_diet_week(profile, week_start="2026-07-20")
    assert meals[0]["cuisine"] == "neutral"


def test_height_and_activity_parsers():
    assert parse_height_cm_from_message("175cm") == 175.0
    assert parse_height_cm_from_message("5'10\"") is not None
    assert parse_activity_level("moderate") == "moderate"
    assert parse_activity_level("light") == "light"
    assert parse_activity_level("Prefer not to say") is None

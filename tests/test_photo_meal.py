"""Photo meal logging + critique skip."""
from app.graph.critique import should_critique
from app.graph.state import CoachingTeamState, UserProfile
from app.tools.meal_vision import (
    CONFIDENCE_THRESHOLD,
    FoodItem,
    MealPhotoAnalysis,
    analysis_needs_clarification,
    foods_ready_to_ground,
)


def test_meal_log_only_skips_critique():
    state = CoachingTeamState(
        intent="nutrition",
        proposals={
            "nutrition": "Logged ~450 kcal and 25g protein from rice and dal.",
            "meal_log_only": True,
        },
        messages=[{"role": "user", "content": "log this photo"}],
    )
    assert should_critique(state) is False


def test_confidence_threshold_gates_grounding():
    low = MealPhotoAnalysis(
        is_food=True,
        foods=[FoodItem(name="rice", estimated_portion="1 cup", confidence=0.4)],
    )
    assert analysis_needs_clarification(low)
    assert foods_ready_to_ground(low) == []

    amb = MealPhotoAnalysis(
        is_food=True,
        foods=[
            FoodItem(
                name="rice",
                estimated_portion="unknown",
                portion_ambiguous=True,
                confidence=0.9,
            )
        ],
    )
    assert analysis_needs_clarification(amb)

    ok = MealPhotoAnalysis(
        is_food=True,
        foods=[
            FoodItem(
                name="rice",
                estimated_portion="1 cup",
                portion_ambiguous=False,
                confidence=CONFIDENCE_THRESHOLD,
            )
        ],
    )
    assert not analysis_needs_clarification(ok)
    assert len(foods_ready_to_ground(ok)) == 1


def test_chat_in_accepts_optional_image_fields():
    from app.main import ChatIn

    body = ChatIn(message="", image_base64="abc", image_mime="image/jpeg")
    assert body.image_base64 == "abc"

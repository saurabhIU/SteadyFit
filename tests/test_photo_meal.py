"""Photo meal logging + critique skip + material ambiguity gate."""
from app.graph.critique import should_critique
from app.graph.state import CoachingTeamState
from app.tools.meal_vision import (
    CONFIDENCE_THRESHOLD,
    FoodItem,
    MealPhotoAnalysis,
    analysis_needs_clarification,
    foods_ready_to_ground,
    is_immaterial_food,
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


def test_material_ambiguity_gates_clarification():
    """Rice portion unknown is material; tomato slices are not."""
    low_main = MealPhotoAnalysis(
        is_food=True,
        foods=[FoodItem(name="rice", estimated_portion="1 cup", confidence=0.4)],
    )
    assert analysis_needs_clarification(low_main)
    assert foods_ready_to_ground(low_main) == []

    amb_rice = MealPhotoAnalysis(
        is_food=True,
        foods=[
            FoodItem(
                name="rice",
                estimated_portion="unknown",
                portion_ambiguous=True,
                confidence=0.9,
                ambiguity_kcal=120,
                ambiguity_protein_g=2,
            )
        ],
    )
    assert analysis_needs_clarification(amb_rice)

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


def test_burger_toppings_do_not_trigger_clarification():
    assert is_immaterial_food("tomato slices")
    assert is_immaterial_food("ketchup")
    assert is_immaterial_food("pickle chips")
    assert not is_immaterial_food("beef burger patty")
    assert not is_immaterial_food("cooked white rice")

    burger = MealPhotoAnalysis(
        is_food=True,
        foods=[
            FoodItem(
                name="beef burger patty",
                estimated_portion="1 patty (~4 oz)",
                portion_ambiguous=False,
                confidence=0.85,
            ),
            FoodItem(
                name="burger bun",
                estimated_portion="1 bun",
                portion_ambiguous=False,
                confidence=0.9,
            ),
            FoodItem(
                name="tomato slices",
                estimated_portion="unknown",
                portion_ambiguous=True,
                confidence=0.4,
                ambiguity_kcal=8,
                ambiguity_protein_g=0.3,
            ),
            FoodItem(
                name="lettuce",
                estimated_portion="1 leaf",
                portion_ambiguous=True,
                confidence=0.5,
            ),
            FoodItem(
                name="mayo",
                estimated_portion="unknown",
                portion_ambiguous=True,
                confidence=0.45,
                ambiguity_kcal=30,
                ambiguity_protein_g=0,
            ),
        ],
    )
    assert not analysis_needs_clarification(burger)
    ready_names = {f.name for f in foods_ready_to_ground(burger)}
    assert "beef burger patty" in ready_names
    assert "tomato slices" in ready_names
    assert "mayo" in ready_names


def test_explicit_small_swing_skips_clarification_for_main_item():
    """Model says swing is under threshold → do not ask even if portion_ambiguous."""
    fries = MealPhotoAnalysis(
        is_food=True,
        foods=[
            FoodItem(
                name="french fries",
                estimated_portion="small handful",
                portion_ambiguous=True,
                confidence=0.7,
                ambiguity_kcal=40,
                ambiguity_protein_g=1,
            )
        ],
    )
    assert not analysis_needs_clarification(fries)
    assert len(foods_ready_to_ground(fries)) == 1


def test_chat_in_accepts_optional_image_fields():
    from app.main import ChatIn

    body = ChatIn(message="", image_base64="abc", image_mime="image/jpeg")
    assert body.image_base64 == "abc"

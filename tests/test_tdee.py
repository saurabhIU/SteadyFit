"""Standalone Mifflin-St Jeor TDEE — independent math assertions."""
from app.graph.tdee import (
    ACTIVITY_FACTORS,
    compute_macro_targets,
    mifflin_st_jeor_bmr,
)


def test_mifflin_male_known_values():
    # 80 kg, 178 cm, 30y male: 10*80 + 6.25*178 - 5*30 + 5 = 800 + 1112.5 - 150 + 5
    bmr = mifflin_st_jeor_bmr(weight_kg=80, height_cm=178, age=30, sex="male")
    assert abs(bmr - 1767.5) < 0.01


def test_mifflin_female_known_values():
    # 65 kg, 165 cm, 28y female: 10*65 + 6.25*165 - 5*28 - 161
    bmr = mifflin_st_jeor_bmr(weight_kg=65, height_cm=165, age=28, sex="female")
    assert abs(bmr - (650 + 1031.25 - 140 - 161)) < 0.01


def test_tdee_moderate_matches_factor():
    out = compute_macro_targets(
        weight_kg=80,
        height_cm=178,
        age=30,
        sex="male",
        activity_level="moderate",
        target_weight_kg=80,
        goal="general fitness",
    )
    expected_bmr = 1767.5
    expected_tdee = expected_bmr * ACTIVITY_FACTORS["moderate"]
    assert out.bmr_kcal == round(expected_bmr)
    assert out.tdee_kcal == round(expected_tdee)
    assert out.calorie_target == round(expected_tdee)  # maintenance
    assert out.is_estimate is False
    assert out.formula == "mifflin_st_jeor"


def test_fat_loss_applies_deficit_band():
    out = compute_macro_targets(
        weight_kg=90,
        height_cm=175,
        age=35,
        sex="male",
        activity_level="light",
        target_weight_kg=80,
        goal="lose fat",
    )
    tdee = out.tdee_kcal
    assert 300 <= (tdee - out.calorie_target) <= 500
    assert out.protein_target_g == round(90 * 2.0)


def test_missing_fields_flagged_as_estimate():
    out = compute_macro_targets(
        weight_kg=75,
        height_cm=None,
        age=None,
        sex=None,
        activity_level=None,
        target_weight_kg=None,
        goal="lose fat",
    )
    assert out.is_estimate is True
    assert "height_missing_default_170cm" in out.estimate_reasons
    assert "activity_missing_default_moderate" in out.estimate_reasons

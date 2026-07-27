"""Deterministic TDEE / macro targets from Mifflin-St Jeor (NutritionScience KB).

Compute in code — agents REPORT these numbers; they must not invent them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActivityLevel = Literal["sedentary", "light", "moderate", "active"]

# KB activity_factors mapped to product enum (sedentary/light/moderate/active).
ACTIVITY_FACTORS: dict[ActivityLevel, float] = {
    "sedentary": 1.2,       # sedentary
    "light": 1.375,         # lightly_active_1_3_days
    "moderate": 1.55,       # moderately_active_3_5_days
    "active": 1.725,        # very_active_6_7_days
}

SexNorm = Literal["male", "female", "other", "unknown"]


@dataclass(frozen=True)
class MacroTargets:
    """Code-computed daily targets — never LLM-narrated."""

    bmr_kcal: int
    tdee_kcal: int
    calorie_target: int
    protein_target_g: int
    activity_factor: float
    activity_level: ActivityLevel | None
    formula: str
    is_estimate: bool
    estimate_reasons: tuple[str, ...]
    notes: str


def normalize_sex(sex: str | None) -> SexNorm:
    if not sex:
        return "unknown"
    s = sex.strip().lower().replace(" ", "_")
    if s in {"m", "male", "man"}:
        return "male"
    if s in {"f", "female", "woman"}:
        return "female"
    if s in {"other", "nonbinary", "non_binary"}:
        return "other"
    if s in {"prefer_not_to_say", "prefer not to say"}:
        return "unknown"
    return "unknown"


def mifflin_st_jeor_bmr(
    *,
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: SexNorm,
) -> float:
    """Mifflin-St Jeor BMR (kcal/day) from NutritionScience.md.

    men:    10×w + 6.25×h − 5×age + 5
    women:  10×w + 6.25×h − 5×age − 161
    other/unknown: average of male and female equations (documented estimate).
    """
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age
    if sex == "male":
        return base + 5.0
    if sex == "female":
        return base - 161.0
    # Midpoint when sex declined/unknown — flagged as estimate upstream.
    return base + (5.0 - 161.0) / 2.0


def _safe_calorie_floor(sex: SexNorm) -> int:
    # KB: do not go below 1500 men / 1200 women without medical supervision.
    if sex == "female":
        return 1200
    if sex == "male":
        return 1500
    return 1350


def compute_macro_targets(
    *,
    weight_kg: float | None,
    height_cm: float | None,
    age: int | None,
    sex: str | None,
    activity_level: ActivityLevel | None,
    target_weight_kg: float | None = None,
    goal: str = "",
) -> MacroTargets:
    """Compute BMR → TDEE → goal-adjusted calorie/protein targets in code.

    Safe rate vs target weight (KB fat_loss 0.3–0.7 kg/week ≈ ~300–500 kcal/day):
    - current > target → deficit of min(500, max(300, ~7700 kcal/kg × gap/week-ish))
      capped to 300–500 kcal/day (not aggressive crash cuts)
    - current < target → surplus 100–250 kcal/day
    - no target / maintain-ish goal → maintenance TDEE
    Protein: fat-loss 2.0 g/kg, hypertrophy 1.8 g/kg, else 1.6 g/kg of *current* weight
    (KB ranges); uses current weight_kg when present.
    """
    reasons: list[str] = []
    sex_n = normalize_sex(sex)
    if sex_n == "unknown":
        reasons.append("sex_unknown_used_midpoint_bmr")

    # Fallbacks when declined — least-imprecise path, clearly estimated.
    w = float(weight_kg) if weight_kg and weight_kg > 0 else None
    h = float(height_cm) if height_cm and height_cm > 0 else None
    a = int(age) if age and age > 0 else None
    if w is None:
        w = 70.0
        reasons.append("weight_missing_default_70kg")
    if h is None:
        h = 170.0
        reasons.append("height_missing_default_170cm")
    if a is None:
        a = 35
        reasons.append("age_missing_default_35")

    act: ActivityLevel = activity_level if activity_level in ACTIVITY_FACTORS else "moderate"
    if activity_level not in ACTIVITY_FACTORS:
        reasons.append("activity_missing_default_moderate")
    factor = ACTIVITY_FACTORS[act]

    bmr = mifflin_st_jeor_bmr(weight_kg=w, height_cm=h, age=a, sex=sex_n)
    tdee = bmr * factor

    goal_l = (goal or "").lower()
    tw = float(target_weight_kg) if target_weight_kg and target_weight_kg > 0 else None

    adjustment = 0.0
    note_bits: list[str] = []
    if tw is not None and abs(w - tw) >= 0.5:
        gap = w - tw  # positive => cut
        if gap > 0 or "lose" in goal_l or "fat" in goal_l or "cut" in goal_l:
            # ~0.5 kg/week ≈ 550 kcal/day; clamp to KB 300–500 sustainable band.
            adjustment = -min(500.0, max(300.0, gap * 110.0))
            note_bits.append(f"deficit {abs(int(adjustment))} kcal toward {tw:g} kg")
        elif gap < 0 or "muscle" in goal_l or "gain" in goal_l or "bulk" in goal_l:
            adjustment = min(250.0, max(100.0, abs(gap) * 80.0))
            note_bits.append(f"surplus {int(adjustment)} kcal toward {tw:g} kg")
    elif "lose" in goal_l or "fat" in goal_l or "cut" in goal_l:
        adjustment = -400.0
        note_bits.append("deficit 400 kcal (goal fat loss, no target weight)")
    elif "muscle" in goal_l or "gain" in goal_l or "bulk" in goal_l:
        adjustment = 150.0
        note_bits.append("surplus 150 kcal (goal muscle gain)")
    else:
        note_bits.append("maintenance TDEE")

    calories = tdee + adjustment
    floor = _safe_calorie_floor(sex_n)
    if calories < floor:
        calories = float(floor)
        note_bits.append(f"floored at {floor} kcal")

    # Protein g/kg current bodyweight (KB).
    if "lose" in goal_l or "fat" in goal_l or "cut" in goal_l:
        protein_per_kg = 2.0
    elif "muscle" in goal_l or "gain" in goal_l or "hypertrophy" in goal_l:
        protein_per_kg = 1.8
    else:
        protein_per_kg = 1.6
    protein = w * protein_per_kg

    is_estimate = bool(reasons)
    return MacroTargets(
        bmr_kcal=int(round(bmr)),
        tdee_kcal=int(round(tdee)),
        calorie_target=int(round(calories)),
        protein_target_g=int(round(protein)),
        activity_factor=factor,
        activity_level=act,
        formula="mifflin_st_jeor",
        is_estimate=is_estimate,
        estimate_reasons=tuple(reasons),
        notes="; ".join(note_bits),
    )

"""Structured 7-day meal plan builder.

Default templates are NEUTRAL, widely-recognizable foods. Indian KB-style examples
are used only when the profile or recent conversation clearly indicates relevance.
"""
from __future__ import annotations

import re
from typing import Any

from app.graph.state import UserProfile

KB_SOURCE_NEUTRAL = "NutritionScience.md — everyday meal patterns"
KB_ID_NEUTRAL = "nutrition_everyday_meals"
KB_SOURCE_INDIAN = "NutritionScience.md — Indian Food Macro Reference"
KB_ID_INDIAN = "nutrition_indian_food_macros"

# (description, kcal, protein_g, tags)
# tags: vegan | vegetarian | eggetarian | nonveg
_NEUTRAL_MEALS: dict[str, list[tuple[str, int, int, set[str]]]] = {
    "breakfast": [
        ("Oatmeal with milk + banana", 320, 12, {"vegetarian", "eggetarian"}),
        ("Greek yogurt + berries + almonds", 280, 18, {"vegetarian", "eggetarian"}),
        ("Scrambled eggs (2) + whole-grain toast", 350, 22, {"eggetarian", "nonveg"}),
        ("Egg-white omelette + fruit", 260, 24, {"eggetarian", "nonveg"}),
        ("Overnight oats with soy milk + fruit", 300, 14, {"vegan", "vegetarian", "eggetarian"}),
        ("Tofu scramble + toast", 320, 18, {"vegan", "vegetarian", "eggetarian"}),
    ],
    "lunch": [
        ("Grilled chicken breast + rice + salad", 520, 40, {"nonveg"}),
        ("Turkey sandwich on whole grain + apple", 480, 32, {"nonveg"}),
        ("Lentil bowl + brown rice + veggies", 500, 22, {"vegan", "vegetarian", "eggetarian"}),
        ("Chickpea salad + quinoa", 470, 20, {"vegan", "vegetarian", "eggetarian"}),
        ("Cottage cheese + fruit + crackers", 420, 28, {"vegetarian", "eggetarian"}),
        ("Bean burrito bowl (no cheese)", 510, 18, {"vegan", "vegetarian", "eggetarian"}),
    ],
    "dinner": [
        ("Baked salmon + potatoes + greens", 520, 36, {"nonveg"}),
        ("Chicken stir-fry + rice", 500, 38, {"nonveg"}),
        ("Tofu stir-fry + rice", 450, 22, {"vegan", "vegetarian", "eggetarian"}),
        ("Pasta with tomato sauce + side salad", 480, 16, {"vegan", "vegetarian", "eggetarian"}),
        ("Veggie omelette + toast", 400, 24, {"eggetarian", "nonveg"}),
        ("Black bean tacos + salsa", 460, 18, {"vegan", "vegetarian", "eggetarian"}),
    ],
    "snack": [
        ("Protein shake in water", 120, 24, {"vegan", "vegetarian", "eggetarian", "nonveg"}),
        ("Apple + peanut butter", 200, 6, {"vegan", "vegetarian", "eggetarian", "nonveg"}),
        ("Greek yogurt cup", 150, 15, {"vegetarian", "eggetarian"}),
        ("Boiled eggs × 2", 156, 12, {"eggetarian", "nonveg"}),
        ("Hummus + carrot sticks", 180, 6, {"vegan", "vegetarian", "eggetarian", "nonveg"}),
    ],
}

_INDIAN_MEALS: dict[str, list[tuple[str, int, int, set[str]]]] = {
    "breakfast": [
        ("Greek dahi + handful almonds + banana", 320, 14, {"vegetarian", "eggetarian"}),
        ("Oats with milk + banana", 280, 10, {"vegetarian", "eggetarian"}),
        ("Egg white omelette (4 whites + 1 yolk) + 2 roti", 380, 28, {"eggetarian", "nonveg"}),
        ("Oats with milk + 2 boiled eggs", 360, 22, {"eggetarian", "nonveg"}),
        ("Soya chunks porridge + fruit", 300, 18, {"vegan", "vegetarian", "eggetarian"}),
        ("Tofu scramble + 2 roti", 340, 20, {"vegan", "vegetarian", "eggetarian"}),
    ],
    "lunch": [
        ("Rajma + brown rice + dahi", 520, 20, {"vegetarian", "eggetarian"}),
        ("Dal + rice + paneer sabzi (150g)", 580, 28, {"vegetarian", "eggetarian"}),
        ("Chole + rice + salad", 500, 18, {"vegan", "vegetarian", "eggetarian"}),
        ("Dal + rice + 150g chicken", 620, 35, {"nonveg"}),
        ("Paneer bhurji + 3 roti", 560, 25, {"vegetarian", "eggetarian"}),
        ("Soya chunks curry + dal + rice", 540, 22, {"vegan", "vegetarian", "eggetarian"}),
    ],
    "dinner": [
        ("Paneer sabzi (150g) + 2 roti + salad", 480, 22, {"vegetarian", "eggetarian"}),
        ("Soya chunks curry + dal + rice", 520, 22, {"vegan", "vegetarian", "eggetarian"}),
        ("Grilled fish + salad + 2 roti", 450, 28, {"nonveg"}),
        ("Chicken curry + 2 roti + dahi", 520, 30, {"nonveg"}),
        ("Tofu stir-fry + 2 roti", 420, 18, {"vegan", "vegetarian", "eggetarian"}),
        ("Dal + 2 roti + Greek dahi", 430, 20, {"vegetarian", "eggetarian"}),
    ],
    "snack": [
        ("Roasted chana 30g", 110, 8, {"vegan", "vegetarian", "eggetarian", "nonveg"}),
        ("Paneer cubes 50g", 130, 9, {"vegetarian", "eggetarian"}),
        ("Boiled eggs × 2", 156, 12, {"eggetarian", "nonveg"}),
        ("Protein shake in water", 120, 24, {"vegan", "vegetarian", "eggetarian", "nonveg"}),
    ],
}

_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

_INDIAN_SIGNAL_RE = re.compile(
    r"(?i)\b("
    r"indian|desi|south\s*asian|punjabi|gujarati|tamil|bengali|"
    r"dal|daal|roti|chapati|paratha|paneer|raita|biryani|masala|"
    r"tandoori|chole|rajma|idli|dosa|sambar|curd\b|dahi\b"
    r")\b"
)


def wants_indian_cuisine(
    profile: UserProfile | None,
    *,
    conversation_text: str = "",
) -> bool:
    """True only when profile/conversation clearly indicates Indian food relevance."""
    bits: list[str] = [conversation_text or ""]
    if profile is not None:
        bits.append(profile.goal or "")
        bits.append(profile.food_preference or "")
        bits.extend(profile.constraints or [])
        bits.append(profile.name or "")
    return bool(_INDIAN_SIGNAL_RE.search(" ".join(bits)))


def _pref_bucket(food_preference: str | None) -> str:
    p = (food_preference or "no-preference").lower()
    if p == "vegan":
        return "vegan"
    if p == "vegetarian":
        return "vegetarian"
    if p == "eggetarian":
        return "eggetarian"
    if p in {"non-vegetarian", "nonvegetarian"}:
        return "nonveg"
    # Neutral default: open omnivore set (not vegetarian-only).
    return "nonveg"


def _allowed(meal_tags: set[str], bucket: str) -> bool:
    if bucket == "vegan":
        return "vegan" in meal_tags
    if bucket == "vegetarian":
        return "vegetarian" in meal_tags or "vegan" in meal_tags
    if bucket == "eggetarian":
        return bool(meal_tags & {"eggetarian", "vegetarian", "vegan"})
    return True  # nonveg / open


def _pick(
    catalog: dict[str, list[tuple[str, int, int, set[str]]]],
    slot: str,
    bucket: str,
    day_index: int,
) -> tuple[str, int, int]:
    options = [m for m in catalog[slot] if _allowed(m[3], bucket)]
    if not options:
        options = [m for m in catalog[slot] if "vegan" in m[3]]
    choice = options[day_index % len(options)]
    return choice[0], choice[1], choice[2]


def build_diet_week(
    profile: UserProfile,
    *,
    week_start: str,
    include_snack: bool = True,
    conversation_text: str = "",
) -> list[dict[str, Any]]:
    """Return diet_plan_days rows (not yet persisted)."""
    indian = wants_indian_cuisine(profile, conversation_text=conversation_text)
    catalog = _INDIAN_MEALS if indian else _NEUTRAL_MEALS
    kb_id = KB_ID_INDIAN if indian else KB_ID_NEUTRAL
    kb_source = KB_SOURCE_INDIAN if indian else KB_SOURCE_NEUTRAL
    bucket = _pref_bucket(profile.food_preference)
    rows: list[dict[str, Any]] = []
    slots = ["breakfast", "lunch", "dinner"] + (["snack"] if include_snack else [])
    for i, day in enumerate(_DAYS):
        for slot in slots:
            desc, kcal, protein = _pick(catalog, slot, bucket, i)
            rows.append({
                "day": day,
                "meal_slot": slot,
                "food_description": desc,
                "kcal": kcal,
                "protein_g": protein,
                "status": "planned",
                "source_kb_id": kb_id,
                "week_start": week_start,
                "citation": f"[KB: {kb_source}]",
                "cuisine": "indian" if indian else "neutral",
            })
    return rows


def diet_plan_contains_nonveg(meals: list[dict[str, Any]]) -> bool:
    banned = ("chicken", "fish", "rohu", "mutton", "meat", "biryani", "turkey", "salmon")
    for m in meals:
        text = (m.get("food_description") or "").lower()
        if any(b in text for b in banned):
            return True
    return False


def diet_plan_violates_preference(
    meals: list[dict[str, Any]],
    food_preference: str | None,
) -> str | None:
    """Return a short critique if meals break the user's food preference."""
    pref = (food_preference or "").lower()
    if not meals or pref in {"", "no-preference", "non-vegetarian", "nonvegetarian"}:
        return None
    if pref in {"vegetarian", "vegan"} and diet_plan_contains_nonveg(meals):
        return (
            f"Profile is {pref} but the diet week includes flesh foods "
            "(chicken/fish/meat). Replace with vegetarian/vegan meals only."
        )
    if pref == "vegan":
        # Whole-word animal dairy/egg — don't flag "soy milk" / "oat milk" / "almond milk".
        for m in meals:
            text = (m.get("food_description") or "").lower()
            if re.search(r"\b(egg|eggs|dahi|paneer|yogurt|yoghurt|ghee|curd|cottage cheese)\b", text):
                return (
                    "Profile is vegan but the diet week includes animal products "
                    "(dairy/eggs). Use vegan meals only."
                )
            if re.search(r"\bmilk\b", text) and not re.search(
                r"\b(soy|oat|almond|coconut|rice)\s+milk\b", text
            ):
                return (
                    "Profile is vegan but the diet week includes animal products "
                    "(dairy/eggs). Use vegan meals only."
                )
    return None


def diet_summary_lines(meals: list[dict[str, Any]], *, max_days: int = 3) -> list[str]:
    """Short bullets for approval card (first few days)."""
    by_day: dict[str, list[str]] = {}
    for m in meals:
        day = m.get("day") or "?"
        slot = m.get("meal_slot") or "meal"
        desc = m.get("food_description") or ""
        by_day.setdefault(day, []).append(f"{slot}: {desc}")
    lines = []
    for day in _DAYS[:max_days]:
        if day in by_day:
            lines.append(f"{day} — " + "; ".join(by_day[day][:3]))
    if len(_DAYS) > max_days:
        lines.append(f"+ meals for {', '.join(_DAYS[max_days:])} (same pattern)")
    cite = (meals[0].get("citation") if meals else None) or f"[KB: {KB_SOURCE_NEUTRAL}]"
    lines.append(f"Sources: {cite}")
    return lines

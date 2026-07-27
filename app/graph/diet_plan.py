"""KB-grounded 7-day meal plan builder (Indian food macros — NutritionScience).

Deterministic templates filtered by food preference — agents report, not invent.
"""
from __future__ import annotations

from typing import Any

from app.graph.state import UserProfile

KB_SOURCE = "NutritionScience.md — Indian Food Macro Reference"
KB_ID = "nutrition_indian_food_macros"

# (description, kcal, protein_g, tags)
# tags: vegan | vegetarian | eggetarian | nonveg
_MEALS: dict[str, list[tuple[str, int, int, set[str]]]] = {
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
    return "vegetarian"  # safe default for unknown


def _allowed(meal_tags: set[str], bucket: str) -> bool:
    if bucket == "vegan":
        return "vegan" in meal_tags
    if bucket == "vegetarian":
        return "vegetarian" in meal_tags or "vegan" in meal_tags
    if bucket == "eggetarian":
        return bool(meal_tags & {"eggetarian", "vegetarian", "vegan"})
    return True  # nonveg / open


def _pick(slot: str, bucket: str, day_index: int) -> tuple[str, int, int]:
    options = [m for m in _MEALS[slot] if _allowed(m[3], bucket)]
    if not options:
        options = [m for m in _MEALS[slot] if "vegan" in m[3]]
    choice = options[day_index % len(options)]
    return choice[0], choice[1], choice[2]


def build_diet_week(
    profile: UserProfile,
    *,
    week_start: str,
    include_snack: bool = True,
) -> list[dict[str, Any]]:
    """Return diet_plan_days rows (not yet persisted)."""
    bucket = _pref_bucket(profile.food_preference)
    rows: list[dict[str, Any]] = []
    slots = ["breakfast", "lunch", "dinner"] + (["snack"] if include_snack else [])
    for i, day in enumerate(_DAYS):
        for slot in slots:
            desc, kcal, protein = _pick(slot, bucket, i)
            rows.append({
                "day": day,
                "meal_slot": slot,
                "food_description": desc,
                "kcal": kcal,
                "protein_g": protein,
                "status": "planned",
                "source_kb_id": KB_ID,
                "week_start": week_start,
                "citation": f"[KB: {KB_SOURCE}]",
            })
    return rows


def diet_plan_contains_nonveg(meals: list[dict[str, Any]]) -> bool:
    banned = ("chicken", "fish", "rohu", "mutton", "meat", "biryani")
    # eggs allowed for eggetarian — only flag clear flesh foods
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
            "(chicken/fish/meat). Replace with vegetarian/vegan KB meals only."
        )
    if pref == "vegan":
        animal = ("egg", "dahi", "paneer", "milk", "yogurt", "ghee", "curd")
        for m in meals:
            text = (m.get("food_description") or "").lower()
            if any(a in text for a in animal):
                return (
                    "Profile is vegan but the diet week includes animal products "
                    "(dairy/eggs). Use vegan KB meals only."
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
        lines.append(f"+ meals for {', '.join(_DAYS[max_days:])} (same KB pattern)")
    lines.append(f"Sources: [KB: {KB_SOURCE}]")
    return lines

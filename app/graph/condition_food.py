"""Condition-aware food-logging nudges — diabetes and hypertension ONLY.

Deliberately narrow scope (per product decision): exactly these two
conditions, deterministic keyword-based food classification, and a
KB-grounded remaining-day suggestion. This is NOT a general
condition-detection system and should not be extended to other conditions
without a fresh product decision.

Runs entirely inside the meal-logging path (``nutrition_node``/
``meal_log_only``) — never touches ``coaching_team``/``plan_changed``, so it
can't collide with the plan-change reply-composition/overwrite class of bugs.
Detection (see ``PersonalPlanContext.health_conditions`` in
``app.graph.personalization``) is off the user's own uploaded docs via
existing retrieval. There is no structured profile field for diagnosed
conditions today; if one is ever added, callers should prefer it over the
doc-detected value before calling into this module.

Tone: informational and caring, never diagnostic/alarming/clinical. No
numbers (no BP readings, no glucose values, no dosing) — general dietary
guidance grounded in SteadyFit's own KB, not medical instruction.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger("steadyfit.condition_food")

DIABETES = "diabetes"
HYPERTENSION = "hypertension"
_KNOWN_CONDITIONS = (DIABETES, HYPERTENSION)

# High-glycemic / high-refined-sugar foods.
_DIABETES_FOOD_RE = re.compile(
    r"(?i)\b("
    r"donut|doughnut|cake|cookies?|candy|soda|pop|cola|"
    r"pastry|pastries|ice\s*cream|milkshake|shake|"
    r"chocolate\s*bar|dessert|sweets?|sugary|syrup|frosting|glazed|"
    r"white\s*bread|white\s*rice|white\s*pasta|"
    r"pancakes?(?:\s*(?:with\s*)?syrup)?|waffles?|sweetened\s*cereal|"
    r"soft\s*drink|energy\s*drink|juice\s*box|fruit\s*juice"
    r")\b"
)

# High-sodium foods: processed/cured meats, most fast food, canned soups,
# salty snacks, pickled foods.
_HYPERTENSION_FOOD_RE = re.compile(
    r"(?i)\b("
    r"chips|fries|pretzels?|salted\s*nuts|salty|instant\s*noodles?|ramen|"
    r"processed\s*meat|cured\s*meat|bacon|sausages?|salami|deli\s*meat|hot\s*dog|"
    r"pickles?|pickled|papad|"
    r"fast\s*food|burger|pizza|"
    r"canned\s*soup|soup\s*\(?canned\)?|soy\s*sauce"
    r")\b"
)

_CONDITION_FOOD_PATTERNS = {
    DIABETES: _DIABETES_FOOD_RE,
    HYPERTENSION: _HYPERTENSION_FOOD_RE,
}

# Targeted queries into the existing curated KB (Volume2 Population Guides —
# Obesity_Diabetes_Office.md already covers both conditions' nutrition notes).
_KB_QUERY = {
    DIABETES: "diabetes low glycemic index diet carb distribution nutrition timing",
    HYPERTENSION: "hypertension high blood pressure sodium diet nutrition notes",
}

# Known-good static citation used only if live KB retrieval is unavailable —
# keeps the nudge deterministic/reliable even if the DB/embeddings hiccup.
_KB_FALLBACK_CITATION = {
    DIABETES: {
        "source_file": "Obesity_Diabetes_Office.md",
        "section": "Nutrition Timing for Diabetics",
        "kb_id": None,
        "snippet": "",
        "tag": "[KB: Obesity_Diabetes_Office.md — Nutrition Timing for Diabetics]",
    },
    HYPERTENSION: {
        "source_file": "Obesity_Diabetes_Office.md",
        "section": "Nutrition Notes (Practical, Non-Clinical)",
        "kb_id": None,
        "snippet": "",
        "tag": "[KB: Obesity_Diabetes_Office.md — Nutrition Notes (Practical, Non-Clinical)]",
    },
}

# Remaining-day suggestions — phrasing mirrors the KB's own guidance
# (glycaemic_index / sodium_awareness + potassium_rich in Volume 2), not
# invented nutrition claims.
_SUGGESTION_CORE = {
    DIABETES: (
        "leaning on lower-GI options like leafy greens, legumes, and other "
        "high-fiber veggies"
    ),
    HYPERTENSION: (
        "favoring fresh vegetables, unsalted proteins, and going easy on "
        "added salt"
    ),
}

_SINGLE_HEADSUP = {
    DIABETES: (
        "Since you've noted diabetes, quick heads up — this one can spike "
        "blood sugar faster than most. No worries, it's tracked."
    ),
    HYPERTENSION: (
        "Since you've noted hypertension, heads up — this one runs high in "
        "sodium. Tracked either way."
    ),
}

_COMBINED_HEADSUP = (
    "Since you've noted diabetes and hypertension, quick heads up — this one "
    "can spike blood sugar and runs high in sodium. No worries, it's tracked "
    "either way."
)


def classify_food_conditions(food_text: str, conditions: list[str]) -> list[str]:
    """Which of the user's noted conditions (diabetes/hypertension) this food

    heuristically conflicts with. Checks are independent, so a food can match
    both (e.g. a salty processed pastry) when the user has both conditions
    noted. Keyword heuristic only — not a nutrition database lookup or
    medical assessment.
    """
    if not food_text or not conditions:
        return []
    noted = {c.lower() for c in conditions if c}
    return [
        label
        for label in _KNOWN_CONDITIONS
        if label in noted and _CONDITION_FOOD_PATTERNS[label].search(food_text)
    ]


def _kb_citation_for(condition: str) -> dict:
    """Best-effort live KB citation grounding the suggestion; falls back to a

    known-good static tag so the nudge is never blocked by a transient
    retrieval failure (DB/embeddings unavailable).
    """
    try:
        from app.rag.retriever import retrieve_kb

        _chunks, cites = retrieve_kb(_KB_QUERY[condition], doc_types=["kb_guide"], k=3)
        for cite in cites:
            if (cite.get("source_file") or "") == "Obesity_Diabetes_Office.md":
                return cite
    except Exception:
        logger.exception("condition_food kb lookup failed condition=%s", condition)
    return _KB_FALLBACK_CITATION[condition]


def build_condition_nudge(risks: list[str]) -> tuple[str, list[dict]]:
    """Deterministic, combined nudge text + KB citation(s) for the matched

    risks. ``risks`` is a subset of [DIABETES, HYPERTENSION]. A food matching
    both conditions gets ONE combined heads-up line (never two stacked
    warnings), followed by a suggestion + citation per condition used.
    Returns ("", []) when risks is empty — callers should not alter the reply.
    """
    ordered = [r for r in _KNOWN_CONDITIONS if r in risks]
    if not ordered:
        return "", []
    citations = [_kb_citation_for(r) for r in ordered]
    headsup = _SINGLE_HEADSUP[ordered[0]] if len(ordered) == 1 else _COMBINED_HEADSUP
    if len(ordered) == 1:
        suggestion = (
            f"For the rest of today, try {_SUGGESTION_CORE[ordered[0]]} "
            f"{citations[0]['tag']}."
        )
    else:
        parts = [
            f"{_SUGGESTION_CORE[r]} {citations[i]['tag']}"
            for i, r in enumerate(ordered)
        ]
        suggestion = f"For the rest of today, try {parts[0]}, and also {parts[1]}."
    return f"{headsup} {suggestion}", citations

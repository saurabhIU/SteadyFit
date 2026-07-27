"""Hard-stop diet metrics gate: weight → target weight → height → activity."""
from __future__ import annotations

import re

from app.graph.state import ACTIVITY_LEVEL_OPTIONS, UserProfile
from app.graph.weight_gate import (  # noqa: F401 — re-export for intake
    WEIGHT_QUESTION,
    looks_like_weight_decline,
    parse_weight_kg_from_message,
)

TARGET_WEIGHT_QUESTION = (
    "What's your target weight? (kg or lb is fine.) "
    "Or tap Prefer not to say — I'll still set sensible starting targets."
)

HEIGHT_QUESTION = (
    "What's your height? (cm, or e.g. 5'10\".) "
    "This locks in a real calorie calculation. Or Prefer not to say."
)

ACTIVITY_QUESTION = (
    "How active are you most weeks outside of training?"
)

ACTIVITY_CHIPS = list(ACTIVITY_LEVEL_OPTIONS) + ["Prefer not to say"]

_HEIGHT_CM_RE = re.compile(r"(?i)^\s*(\d{2,3}(?:\.\d+)?)\s*cm\s*$")
_HEIGHT_BARE_RE = re.compile(r"^\s*(\d{2,3}(?:\.\d+)?)\s*$")
_HEIGHT_FT_RE = re.compile(
    r"(?i)^\s*(\d)\s*[\'′]\s*(\d{1,2})(?:\s*[\"″])?\s*$"
    r"|^\s*(\d)\s*ft(?:\s*(\d{1,2})\s*in)?\s*$"
)


def parse_height_cm_from_message(message: str) -> float | None:
    text = (message or "").strip()
    if not text or looks_like_weight_decline(text):
        return None
    m = _HEIGHT_CM_RE.match(text) or _HEIGHT_BARE_RE.match(text)
    if m:
        cm = float(m.group(1))
        # Bare 55–90 is more likely inches misread — require cm or feet form.
        if _HEIGHT_BARE_RE.match(text) and cm < 120:
            return None
        if 120 <= cm <= 230:
            return round(cm, 1)
        return None
    m = _HEIGHT_FT_RE.match(text)
    if m:
        feet = int(m.group(1) or m.group(3) or 0)
        inches = int(m.group(2) or m.group(4) or 0)
        cm = feet * 30.48 + inches * 2.54
        if 120 <= cm <= 230:
            return round(cm, 1)
    return None


def parse_activity_level(message: str) -> str | None:
    raw = (message or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "sedentary": "sedentary",
        "light": "light",
        "lightly_active": "light",
        "lightlyactive": "light",
        "moderate": "moderate",
        "moderately_active": "moderate",
        "active": "active",
        "very_active": "active",
    }
    return aliases.get(raw)


def slot_resolved(profile: UserProfile, slot: str) -> bool:
    if slot == "weight":
        return profile.weight_kg is not None or profile.weight_declined
    if slot == "target_weight":
        return profile.target_weight_kg is not None or profile.target_weight_declined
    if slot == "height":
        return profile.height_cm is not None or profile.height_declined
    if slot == "activity":
        return bool(profile.activity_level) or profile.activity_declined
    return True


def next_diet_slot(profile: UserProfile) -> str | None:
    for slot in ("weight", "target_weight", "height", "activity"):
        if not slot_resolved(profile, slot):
            return slot
    return None


def diet_gate_active(profile: UserProfile) -> bool:
    return bool(
        profile.awaiting_weight_for_first_plan
        or profile.awaiting_diet_slot
        or next_diet_slot(profile)
    )


def question_for_slot(slot: str) -> tuple[str, list[str]]:
    if slot == "weight":
        return WEIGHT_QUESTION, ["Prefer not to say"]
    if slot == "target_weight":
        return TARGET_WEIGHT_QUESTION, ["Prefer not to say"]
    if slot == "height":
        return HEIGHT_QUESTION, ["Prefer not to say"]
    if slot == "activity":
        return ACTIVITY_QUESTION, ACTIVITY_CHIPS
    return "Tell me a bit more so I can set your targets.", ["Prefer not to say"]


def diet_question_payload(profile: UserProfile, slot: str) -> dict:
    """Ask one diet-metrics question and end the turn (no plan)."""
    updated = profile.model_copy(deep=True)
    q, chips = question_for_slot(slot)
    if slot == "weight":
        updated.awaiting_weight_for_first_plan = True
        updated.awaiting_diet_slot = None
    else:
        updated.awaiting_weight_for_first_plan = False
        updated.awaiting_diet_slot = slot
    return {
        "profile": updated,
        "intent": "intake",
        "quick_replies": chips,
        "messages": [{"role": "assistant", "content": q}],
        "proposals": {
            "ask_diet_slot": slot,
            "ask_weight_only": slot == "weight",
            "plan_changed": False,
        },
    }


def needs_diet_gate_before_first_plan(
    profile: UserProfile | None,
    *,
    week_plan=None,
    saved_plan=None,
) -> bool:
    from app.graph.approval_copy import has_prior_week_plan

    if profile is None:
        return False
    if has_prior_week_plan(week_plan) or has_prior_week_plan(saved_plan):
        return False
    return next_diet_slot(profile) is not None

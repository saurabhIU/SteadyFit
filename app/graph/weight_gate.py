"""Hard gate: ask weight before first WeekPlan generation (not decorative prose)."""
from __future__ import annotations

import re

from app.graph.approval_copy import has_prior_week_plan
from app.graph.macros import has_body_stats
from app.graph.state import UserProfile, WeekPlan

WEIGHT_QUESTION = (
    "Before I draft your first week — what's your current weight? "
    "(kg or lb is fine.) I'll use it to set calorie and protein targets. "
    "Or tap Prefer not to say and I'll use starting estimates."
)

# When the user thinks weight is already elsewhere (upload/doc) — ack, then ask
# directly. Does NOT retrieve or extract from documents.
WEIGHT_ACK_REASK = (
    "Got it — I've noted that. For your weight specifically, I'll need you to "
    "tell me directly so I can set accurate targets. What is it?"
)

WEIGHT_DECLINE_RE = re.compile(
    r"(?i)\b("
    r"prefer not to say|rather not say|skip(?:\s+it)?|no thanks|"
    r"don'?t want to (?:say|share)|not sharing|pass|"
    r"none of your business|decline"
    r")\b"
)

# Cheap cue that the user believes the answer is already available elsewhere.
_ALREADY_ELSEWHERE_RE = re.compile(
    r"(?i)\b("
    r"upload(?:ed)?|document|\bdocs?\b|\bfile\b|"
    r"you should know|already (?:told|gave|shared|said|provided)|"
    r"i already|"
    r"it'?s in (?:my |the )?(?:doc|document|upload|file)|"
    r"check (?:my |the )?(?:doc|document|upload|file)|"
    r"from (?:my |the )?(?:doc|document|upload|file)|"
    r"in (?:my |the )?(?:doc|document|upload|file)"
    r")\b"
)

_FIRST_PLAN_ASK_RE = re.compile(
    r"(?i)\b("
    r"first week|draft my (?:first )?week|build my (?:first )?week|"
    r"generate my (?:first )?week|starting plan|create my plan|"
    r"make me a plan|my first plan|first week plan|plan to confirm"
    r")\b"
)


def needs_weight_before_first_plan(
    profile: UserProfile | None,
    *,
    week_plan: WeekPlan | None = None,
    saved_plan: WeekPlan | None = None,
) -> bool:
    """True only for first-ever plan when weight unknown and not yet declined."""
    if profile is None:
        return False
    if has_prior_week_plan(week_plan) or has_prior_week_plan(saved_plan):
        return False
    if has_body_stats(profile):
        return False
    if profile.weight_declined:
        return False
    return True


def looks_like_weight_decline(message: str) -> bool:
    return bool(WEIGHT_DECLINE_RE.search(message or ""))


def looks_like_weight_already_elsewhere(message: str) -> bool:
    """True when the user implies weight is already in a doc/upload/prior answer.

    Heuristic only — never triggers document retrieval or field extraction.
    """
    return bool(_ALREADY_ELSEWHERE_RE.search(message or ""))


def looks_like_first_plan_request(message: str) -> bool:
    return bool(_FIRST_PLAN_ASK_RE.search(message or ""))


_WEIGHT_VALUE_RE = re.compile(
    r"(?i)(?:^|\b)(\d{2,3}(?:\.\d+)?)\s*(kg|kgs|kilos?|lb|lbs|pounds?)?\b"
)


def parse_weight_kg_from_message(message: str) -> float | None:
    """Deterministic weight parse for the gated turn (kg or lb)."""
    text = (message or "").strip()
    if not text or looks_like_weight_decline(text):
        return None
    m = _WEIGHT_VALUE_RE.search(text)
    if not m:
        return None
    value = float(m.group(1))
    unit = (m.group(2) or "kg").lower()
    if unit.startswith("lb") or unit.startswith("pound"):
        value *= 0.45359237
    if value < 30.0 or value > 300.0:
        return None
    return round(value, 1)


def weight_question_payload(profile: UserProfile) -> dict:
    """Return graph update that asks for weight and ends the turn (no plan)."""
    updated = profile.model_copy(deep=True)
    updated.awaiting_weight_for_first_plan = True
    return {
        "profile": updated,
        "intent": "intake",
        "quick_replies": ["Prefer not to say"],
        "messages": [{"role": "assistant", "content": WEIGHT_QUESTION}],
        "proposals": {
            "ask_weight_only": True,
            # Never carry plan-change flags into this turn.
            "plan_changed": False,
        },
    }

"""Adherence check-in → schedule-adjustment continuation (chip + detectors)."""
from __future__ import annotations

import re

from app.graph.approval_copy import has_prior_week_plan
from app.graph.state import UserProfile, WeekPlan

# Internal routing token (legacy + detector). Display label answers
# "should we adjust now?" — see YES_SCHEDULE_CHIP_LABEL.
YES_SCHEDULE_CHIP = "yes schedule"
YES_SCHEDULE_CHIP_LABEL = "yes, adjust"

# Chip taps and close paraphrases accepting a dial-back / re-plan offer.
_YES_SCHEDULE_RE = re.compile(
    r"(?is)^\s*("
    r"yes(?:[,.]?\s+)?(?:please\s+)?schedule|"
    r"yes[,.]?\s+(?:please\s+)?(?:let'?s\s+)?(?:re-?)?schedule|"
    r"yes[,.]?\s+(?:dial|simplify|adjust)|"
    r"yes[,.]?\s+let'?s\s+(?:dial|simplify|adjust|re-?plan)|"
    r"schedule\s+(?:it|please)|"
    r"let'?s\s+(?:simplify|re-?plan|dial\s+(?:it|things?)\s+back)"
    r")\s*[.!]?\s*$"
)

# Prior coach check-in offered a schedule simplification / re-plan.
_ADHERENCE_SCHEDULE_OFFER_RE = re.compile(
    r"(?is)("
    r"dial\s+things?\s+back|"
    r"simplify(?:\s+(?:your|the|this))?\s+(?:week|plan)|"
    r"lighter\s+week|"
    r"fewer\s+(?:sessions|workouts)|"
    r"shorten(?:\s+(?:your|the|gym))?\s+(?:sessions|workouts)|"
    r"want\s+me\s+to\s+(?:re-?)?plan|"
    r"if\s+you\s+want[^.!?]{0,80}(?:dial|simplify|re-?plan|adjust|schedule)|"
    r"can\s+(?:re-?)?schedule|"
    r"adjust\s+(?:your|the|this)\s+(?:week|plan|schedule)|"
    r"should\s+we\s+adjust|"
    r"yes(?:[,.]?\s+)?(?:schedule|adjust)"
    r")"
)

# New-user intake questions the Scheduler must never ask returning users.
CLARIFYING_INTAKE_RE = re.compile(
    r"(?is)("
    r"experience\s+level|"
    r"beginner[,/\s]+(?:intermediate|advanced)|"
    r"session\s+duration|"
    r"how\s+long\s+(?:are|do|should)\s+(?:your|the)\s+sessions|"
    r"(?:any\s+)?injuries?\s*(?:/|or|&)?\s*limitations|"
    r"any\s+(?:injuries|limitations)\b|"
    r"what(?:'s|\s+is)\s+your\s+experience"
    r")"
)


def looks_like_yes_schedule_chip(message: str) -> bool:
    """True for the adjust-now chip (label or internal value) and close paraphrases."""
    t = (message or "").strip().lower()
    if not t:
        return False
    if t in {
        YES_SCHEDULE_CHIP,
        YES_SCHEDULE_CHIP_LABEL,
        "yes, schedule",
        "yes please schedule",
        "yes, please schedule",
        "yes adjust",
    }:
        return True
    return bool(_YES_SCHEDULE_RE.match(message or ""))


def prior_was_adherence_schedule_offer(prior_assistant: str | None) -> bool:
    """Prior coach message offered to dial back / re-plan the week."""
    if not (prior_assistant or "").strip():
        return False
    return bool(_ADHERENCE_SCHEDULE_OFFER_RE.search(prior_assistant))


def is_returning_schedule_user(
    profile: UserProfile | None,
    week_plan: WeekPlan | None,
    *,
    saved_plan: WeekPlan | None = None,
) -> bool:
    """Complete onboarding + an existing week plan → never re-run intake Qs."""
    if profile is None or not profile.onboarding_complete:
        return False
    return has_prior_week_plan(week_plan) or has_prior_week_plan(saved_plan)


def reply_asks_clarifying_intake(reply: str) -> bool:
    return bool(CLARIFYING_INTAKE_RE.search(reply or ""))

"""One-time upload choice before the diet weight-gate chain.

intake → END (no council). Separate from the retired post-handoff soft hint.
"""
from __future__ import annotations

import re

from app.graph.diet_gate import diet_question_payload
from app.graph.state import UserProfile
from app.memory.store import user_has_personal_docs

UPLOAD_BEFORE_WEIGHT_QUESTION = (
    "Before I ask a few quick numbers — do you have a program or health "
    "notes written down?"
)
UPLOAD_NOW_CHIP = "Upload it now"
JUST_ASK_CHIP = "Just ask me"
UPLOAD_NOW_INSTRUCT = (
    "Head to the Update tab, upload it, then just say 'ready' "
    "(or ask me anything) and I'll pick up from there."
)

_UPLOAD_NOW_RE = re.compile(
    r"(?is)^\s*(upload(?:\s+it)?\s+now|upload\s+now|i'?ll\s+upload)\s*[.!?]?\s*$"
)
_JUST_ASK_RE = re.compile(
    r"(?is)^\s*(just\s+ask(?:\s+me)?|ask\s+me|no\s+upload|skip\s+upload)\s*[.!?]?\s*$"
)
_READY_RE = re.compile(
    r"(?is)^\s*(ready|i'?m\s+ready|all\s+set|done\s+uploading|uploaded)\s*[.!?]?\s*$"
)


def looks_like_upload_now(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw.lower() == UPLOAD_NOW_CHIP.lower():
        return True
    return bool(_UPLOAD_NOW_RE.match(raw))


def looks_like_just_ask(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw.lower() == JUST_ASK_CHIP.lower():
        return True
    return bool(_JUST_ASK_RE.match(raw))


def looks_like_ready_after_upload(text: str) -> bool:
    return bool(_READY_RE.match((text or "").strip()))


def upload_offer_payload(profile: UserProfile) -> dict:
    """Present the upload choice; do not open the weight slot yet."""
    updated = profile.model_copy(deep=True)
    updated.awaiting_upload_before_weight = True
    # Clear weight-gate waiters so we don't parse this turn as a weight answer.
    updated.awaiting_weight_for_first_plan = False
    if updated.awaiting_diet_slot == "upload_offer":
        updated.awaiting_diet_slot = None
    return {
        "profile": updated,
        "intent": "intake",
        "quick_replies": [UPLOAD_NOW_CHIP, JUST_ASK_CHIP],
        "messages": [{"role": "assistant", "content": UPLOAD_BEFORE_WEIGHT_QUESTION}],
        "proposals": {
            "ask_upload_before_weight": True,
            "plan_changed": False,
        },
    }


def _mark_offered(profile: UserProfile) -> UserProfile:
    updated = profile.model_copy(deep=True)
    updated.offered_upload_before_weight_gate = True
    updated.awaiting_upload_before_weight = False
    return updated


def weight_after_offer(profile: UserProfile) -> dict:
    """Close the offer branch and ask current weight."""
    updated = _mark_offered(profile)
    return diet_question_payload(updated, "weight")


def upload_now_instruct_payload(profile: UserProfile) -> dict:
    """User chose upload — instruct, set flag, arm normal weight-gate for next turn."""
    updated = _mark_offered(profile)
    # Next message should re-enter intake via the existing weight-gate waiter.
    updated.awaiting_weight_for_first_plan = True
    return {
        "profile": updated,
        "intent": "intake",
        "quick_replies": [],
        "messages": [{"role": "assistant", "content": UPLOAD_NOW_INSTRUCT}],
        "proposals": {
            "ask_diet_slot": "weight",
            "ask_weight_only": True,
            "plan_changed": False,
        },
    }


def ambiguous_reoffer_payload(profile: UserProfile, *, aside: str = "") -> dict:
    """Brief answer + re-show the offer chips (flag still unset)."""
    updated = profile.model_copy(deep=True)
    updated.awaiting_upload_before_weight = True
    updated.awaiting_weight_for_first_plan = False
    body = UPLOAD_BEFORE_WEIGHT_QUESTION
    if aside.strip():
        body = f"{aside.strip()}\n\n{UPLOAD_BEFORE_WEIGHT_QUESTION}"
    return {
        "profile": updated,
        "intent": "intake",
        "quick_replies": [UPLOAD_NOW_CHIP, JUST_ASK_CHIP],
        "messages": [{"role": "assistant", "content": body}],
        "proposals": {
            "ask_upload_before_weight": True,
            "plan_changed": False,
        },
    }


def maybe_upload_offer_or_weight(profile: UserProfile, user_id: str) -> dict:
    """Entry to the weight gate: offer once (if no docs), else ask weight."""
    if profile.offered_upload_before_weight_gate:
        return diet_question_payload(profile, "weight")
    if user_has_personal_docs(user_id):
        updated = _mark_offered(profile)
        return diet_question_payload(updated, "weight")
    return upload_offer_payload(profile)


def open_first_diet_slot(profile: UserProfile, user_id: str, slot: str | None = None) -> dict:
    """Open weight (via offer) or a later diet slot."""
    from app.graph.diet_gate import next_diet_slot

    resolved = slot or next_diet_slot(profile) or "weight"
    if resolved == "weight":
        return maybe_upload_offer_or_weight(profile, user_id)
    return diet_question_payload(profile, resolved)

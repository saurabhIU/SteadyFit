"""Copy for the HITL plan-approval card (first plan vs tweak)."""
from __future__ import annotations

from typing import Any

# Post-accept / post-reject chat replies — short only. Never reuse the
# pre-approval proposal body (personalization note, look-below CTA, diffs).
APPROVE_ACCEPT_REPLY = "Plan approved and saved — you're set for the week."
APPROVE_REJECT_REPLY_TWEAK = (
    "No worries — kept your previous plan. "
    "Tell me if you want a different adjustment."
)
APPROVE_REJECT_REPLY_FIRST = (
    "No worries — we won't lock a week in yet. "
    "Tell me when you want to try a first-week draft again."
)


def approve_decision_reply(decision: str, *, is_first_plan: bool = False) -> str:
    """Canonical short confirmation after HITL accept/reject."""
    action = (decision or "").strip().lower()
    if action == "accept":
        return APPROVE_ACCEPT_REPLY
    if is_first_plan:
        return APPROVE_REJECT_REPLY_FIRST
    return APPROVE_REJECT_REPLY_TWEAK


def has_prior_week_plan(plan: Any) -> bool:
    """True when a real WeekPlan with scheduled days already exists."""
    if plan is None:
        return False
    days = getattr(plan, "days", None)
    if days is None and isinstance(plan, dict):
        days = plan.get("days")
    return bool(days)


def plan_approval_framing(*, has_prior: bool) -> dict[str, str | bool]:
    """Headline/subhead for the approval card based on prior WeekPlan existence."""
    if not has_prior:
        return {
            "is_first_plan": True,
            "headline": "Here's your first week",
            "subhead": (
                "The AI Coaching Team drafted this starting plan — "
                "only if it works for you."
            ),
        }
    return {
        "is_first_plan": False,
        "headline": "A small tweak to your week",
        "subhead": (
            "The AI Coaching Team lined up these adjustments — "
            "only if they work for you."
        ),
    }

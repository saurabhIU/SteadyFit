"""Copy for the HITL plan-approval card (first plan vs tweak)."""
from __future__ import annotations

from typing import Any


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

"""Persist a coaching-memory summary after weekly review (or noop)."""
from __future__ import annotations

import logging
from datetime import date

from app.graph.state import CoachingTeamState
from app.memory.weekly_summary import (
    extract_user_texts,
    generate_weekly_summary,
    previous_week_start,
)
from app.rag.memory_store import upsert_weekly_memory
from app.security import as_text

logger = logging.getLogger("steadyfit.memory_write")


def is_weekly_review_turn(state: CoachingTeamState) -> bool:
    for m in state.messages or []:
        content = getattr(m, "content", None)
        if content is None and isinstance(m, dict):
            content = m.get("content")
        blob = as_text(content).upper()
        if "SYSTEM_TRIGGER" in blob and "WEEKLY" in blob:
            return True
        if "WEEKLY REVIEW" in blob and "SYSTEM_TRIGGER" in blob:
            return True
    return False


def memory_write_node(state: CoachingTeamState) -> dict:
    """After coaching_team: summarize the completed week into doc_type=memory."""
    if not is_weekly_review_turn(state):
        return {}
    prior = state.proposals.get("memory_written")
    if prior and prior != "error":
        return {}  # already persisted this review turn

    week_start = previous_week_start()
    if state.week_plan and state.week_plan.week_start:
        try:
            plan_ws = date.fromisoformat(state.week_plan.week_start[:10])
            if plan_ws <= week_start:
                week_start = plan_ws
        except ValueError:
            pass

    try:
        if not state.user_id:
            logger.warning("memory_write skipped: missing user_id")
            return {}
        summary = generate_weekly_summary(
            week_start,
            user_id=state.user_id,
            week_plan=state.week_plan,
            proposals=state.proposals,
            user_messages=extract_user_texts(list(state.messages)),
            risk_flag=state.risk_flag,
        )
        src = upsert_weekly_memory(summary, state.user_id)
        logger.info("memory_write ok source_file=%s", src)
        return {"proposals": {**state.proposals, "memory_written": src}}
    except Exception:
        logger.exception("memory_write failed week=%s", week_start)
        return {"proposals": {**state.proposals, "memory_written": "error"}}

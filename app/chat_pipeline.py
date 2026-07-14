"""Shared chat processing: normalize → scope gate → LangGraph (or refuse)."""
from __future__ import annotations

import logging
import uuid

from app.graph.intake import needs_intake
from app.graph.response import build_chat_payload
from app.graph.runtime import thread_config
from app.memory.context import bootstrap_input
from app.memory.store import get_profile
from app.security import (
    OUT_OF_SCOPE_REPLY,
    classify_scope,
    log_out_of_scope,
    normalize_user_message,
    out_of_scope_reply,
)

logger = logging.getLogger("steadyfit.chat")


def process_user_chat(graph, message: str, thread_id: str | None = None) -> dict:
    """Run defenses then the coaching team graph. Used by API and evals."""
    thread = thread_id or str(uuid.uuid4())
    normalized = normalize_user_message(message)
    if not normalized:
        return {
            "thread_id": thread,
            "reply": OUT_OF_SCOPE_REPLY,
            "coaching_team": {},
            "pending_approval": None,
            "quick_replies": [],
            "scope": "rejected_empty",
        }

    # During onboarding, short answers ("3", "vegan") must not be OOS-blocked.
    profile = get_profile()
    if needs_intake(profile) and not profile.onboarding_complete:
        verdict = "in_scope"
    else:
        verdict = classify_scope(normalized)
        if verdict == "out_of_scope":
            log_out_of_scope(thread_id=thread, message=normalized, verdict=verdict)
            return {
                "thread_id": thread,
                "reply": out_of_scope_reply(normalized),
                "coaching_team": {},
                "pending_approval": None,
                "quick_replies": [],
                "scope": verdict,
            }

    config = thread_config(thread)
    result = graph.invoke(
        bootstrap_input(
            graph,
            thread,
            messages=[{"role": "user", "content": normalized}],
        ),
        config=config,
    )
    payload = build_chat_payload(thread, result, graph=graph, config=config)
    payload["scope"] = verdict
    return payload

"""Dedicated quick-workout Done / replace / extra — bypasses the chat pipeline."""
from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage

from app.graph.micro_workout import (
    EXTRA_CHIP,
    REPLACE_CHIP,
    handle_quick_10_choice,
    handle_quick_10_done,
    resolve_today_plan_context,
)
from app.graph.runtime import make_thread_id, thread_config
from app.memory.context import week_plan_from_graph
from app.memory.store import get_profile, get_saved_week_plan
from app.memory.user_context import set_current_user_id

QuickWorkoutAction = Literal["done", "replace", "extra"]


def run_quick_workout_action(
    graph,
    *,
    user_id: str,
    action: QuickWorkoutAction,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Log / resolve a 10-minute session without chat, intake, or coach routing.

    Reuses handle_quick_10_done / handle_quick_10_choice. Appends only the
    confirmation assistant message to the thread — never a synthetic "done"
    user turn that could be extracted into profile slots.
    """
    set_current_user_id(user_id)
    conversation = (conversation_id or "default").strip() or "default"
    thread = make_thread_id(user_id, conversation)
    config = thread_config(thread, user_id=user_id, endpoint="api/quick-workout")

    profile = get_profile(user_id)
    week_plan = week_plan_from_graph(graph, thread) or get_saved_week_plan(user_id)
    today_case = resolve_today_plan_context(week_plan).case

    if action == "done":
        result = handle_quick_10_done(
            user_id=user_id,
            profile=profile,
            week_plan=week_plan,
        )
    elif action in {"replace", "extra"}:
        result = handle_quick_10_choice(
            user_id=user_id,
            profile=profile,
            week_plan=week_plan,
            choice=action,  # type: ignore[arg-type]
        )
    else:
        raise ValueError(f"unsupported quick-workout action: {action}")

    # Persist confirmation in thread history without going through coach/intake.
    try:
        graph.update_state(
            config,
            {
                "messages": [AIMessage(content=result.reply)],
                # Clear chat-pipeline micro flags so a later free-text "done"
                # cannot be mistaken for a structured action.
                "proposals": {
                    "micro_session": False,
                    "micro_done": False,
                    "awaiting_quick_10_choice": result.awaiting_choice,
                    "micro_session_log": True,
                },
                "quick_replies": list(result.quick_replies),
            },
        )
        if result.week_plan is not None:
            graph.update_state(config, {"week_plan": result.week_plan})
    except Exception:
        # Logging already succeeded; history append is best-effort.
        pass

    return {
        "thread_id": thread,
        "user_id": user_id,
        "reply": result.reply,
        "quick_replies": list(result.quick_replies),
        "logged": bool(result.logged),
        "awaiting_choice": bool(result.awaiting_choice),
        "case": today_case,
        "action": action,
        "pending_approval": None,
        "coaching_team": {},
        "citations": [],
        "scope": "quick_workout_action",
        "replace_chip": REPLACE_CHIP,
        "extra_chip": EXTRA_CHIP,
    }

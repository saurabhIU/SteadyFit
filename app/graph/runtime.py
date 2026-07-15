"""LangGraph runtime helpers."""
from __future__ import annotations

from langchain_core.runnables import RunnableConfig


def make_thread_id(user_id: str, conversation_id: str) -> str:
    """Namespace checkpointer threads: ``{user_id}:{conversation_id}``."""
    conv = conversation_id.strip()
    prefix = f"{user_id}:"
    if conv.startswith(prefix):
        return conv
    # Drop a different user's namespace so profile switches cannot leak threads.
    if ":" in conv:
        maybe_user, rest = conv.split(":", 1)
        if maybe_user and maybe_user != user_id:
            conv = rest
    return f"{user_id}:{conv}"


def conversation_id_from_thread(thread_id: str) -> str:
    if ":" in thread_id:
        return thread_id.split(":", 1)[1]
    return thread_id


def user_id_from_thread(thread_id: str) -> str | None:
    if ":" in thread_id:
        return thread_id.split(":", 1)[0]
    return None


def weekly_review_thread(user_id: str) -> str:
    return make_thread_id(user_id, "weekly-review")


def thread_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}

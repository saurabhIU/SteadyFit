"""Normalize LangGraph invoke results into API-friendly payloads."""
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.serde.types import INTERRUPT

from app.graph.runtime import thread_config


def _as_dict(state: Any) -> dict:
    if state is None:
        return {}
    if hasattr(state, "model_dump"):
        return state.model_dump()
    if isinstance(state, dict):
        return state
    return {}


def extract_interrupts(result: Any) -> list:
    if isinstance(result, dict) and INTERRUPT in result:
        return list(result[INTERRUPT])
    if hasattr(result, "interrupts"):
        return list(result.interrupts)
    return []


def extract_state(result: Any) -> Any:
    if isinstance(result, dict) and INTERRUPT in result and len(result) == 1:
        return None
    if hasattr(result, "value"):
        return result.value
    return result


def pending_approval_from_interrupts(interrupts: list) -> dict | None:
    if not interrupts:
        return None
    first = interrupts[0]
    value = first.value if hasattr(first, "value") else first.get("value")
    if isinstance(value, dict) and value.get("type") == "plan_approval":
        return value
    return None


def last_message_content(state: Any) -> str:
    data = _as_dict(state)
    messages = data.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    if hasattr(last, "content"):
        return str(last.content)
    if isinstance(last, dict):
        return str(last.get("content", ""))
    return str(last)


def proposals_from_state(state: Any) -> dict:
    data = _as_dict(state)
    proposals = dict(data.get("proposals") or {})
    proposals.pop("plan_changed", None)
    proposals.pop("proposed_week_plan", None)
    return proposals


def _message_role_content(message: Any) -> dict | None:
    if isinstance(message, dict):
        role = message.get("role")
        content = message.get("content", "")
        if role not in ("user", "assistant"):
            return None
        text = str(content)
    else:
        msg_type = (getattr(message, "type", None) or message.__class__.__name__).lower()
        if "human" in msg_type or msg_type == "user":
            role = "user"
        elif "ai" in msg_type or msg_type == "assistant":
            role = "assistant"
        else:
            return None
        content = getattr(message, "content", "")
        text = str(content)

    if role == "user" and text.startswith("SYSTEM_TRIGGER:"):
        return None
    if not text.strip():
        return None
    return {"role": role, "content": text}


def messages_from_state(state: Any) -> list[dict]:
    data = _as_dict(state)
    raw_messages = data.get("messages") or []
    messages: list[dict] = []
    for message in raw_messages:
        parsed = _message_role_content(message)
        if parsed:
            messages.append(parsed)
    return messages


def pending_approval_from_snapshot(snapshot: Any) -> dict | None:
    if snapshot is None:
        return None
    interrupts = getattr(snapshot, "interrupts", None) or ()
    return pending_approval_from_interrupts(list(interrupts))


def build_thread_history(graph, thread_id: str) -> dict:
    snapshot = graph.get_state(thread_config(thread_id))
    if not snapshot or not snapshot.values:
        return {"thread_id": thread_id, "messages": [], "pending_approval": None}

    state = snapshot.values
    messages = messages_from_state(state)
    pending = pending_approval_from_snapshot(snapshot)

    return {
        "thread_id": thread_id,
        "messages": messages,
        "pending_approval": pending,
    }


def build_chat_payload(
    thread_id: str,
    result: Any,
    *,
    graph=None,
    config: RunnableConfig | None = None,
) -> dict:
    interrupts = extract_interrupts(result)
    state = extract_state(result)
    pending = pending_approval_from_interrupts(interrupts)

    if pending and graph is not None and config is not None:
        snapshot = graph.get_state(config)
        state = snapshot.values

    reply = last_message_content(state)
    # Specialist drafts are merged into the coach reply — don't echo them again.
    council = {} if reply else proposals_from_state(state)

    return {
        "thread_id": thread_id,
        "reply": reply,
        "council": council,
        "pending_approval": pending,
    }

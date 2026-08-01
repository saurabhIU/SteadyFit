"""Shared chat processing: normalize → scope gate → LangGraph (or refuse)."""
from __future__ import annotations

import logging
import uuid

from langgraph.types import Command
from langsmith import traceable

from app.graph.intake import needs_intake
from app.graph.response import (
    build_chat_payload,
    messages_from_state,
    pending_approval_from_snapshot,
)
from app.graph.runtime import make_thread_id, thread_config
from app.memory.context import bootstrap_input, persist_approved_plan
from app.memory.store import get_profile
from app.memory.user_context import set_current_user_id
from app.security import (
    OUT_OF_SCOPE_REPLY,
    UI_WELCOME_PRIOR,
    classify_scope,
    gentle_clarification_reply,
    is_first_user_turn,
    log_out_of_scope,
    looks_like_fitness_query,
    looks_like_short_affirmation,
    looks_like_short_reject,
    normalize_user_message,
    out_of_scope_reply,
    prior_turns_from_messages,
)

logger = logging.getLogger("steadyfit.chat")

CHAT_ENDPOINT = "api/chat"


def _snapshot_messages(graph, thread: str) -> list[dict]:
    try:
        snapshot = graph.get_state(thread_config(thread))
    except Exception:
        return []
    if not snapshot or not getattr(snapshot, "values", None):
        return []
    return messages_from_state(snapshot.values)


def _pending_approval(graph, thread: str):
    try:
        snapshot = graph.get_state(thread_config(thread))
    except Exception:
        return None
    return pending_approval_from_snapshot(snapshot)


def should_skip_scope_gate(
    *,
    profile,
    pending_approval: dict | None,
    history: list | None = None,
) -> bool:
    """Deterministic bypass when the system explicitly asked for this reply.

    Also bypasses on the very first user turn in a thread (UI greeting is not
    persisted). Callers must still refuse clear off-topic asks on that path.
    """
    if pending_approval and pending_approval.get("type") == "plan_approval":
        return True
    if needs_intake(profile) and not profile.onboarding_complete:
        return True
    if profile.awaiting_onboarding_confirm:
        return True
    if getattr(profile, "awaiting_weight_for_first_plan", False):
        return True
    if getattr(profile, "awaiting_diet_slot", None):
        return True
    if getattr(profile, "awaiting_upload_before_weight", False):
        return True
    if history is not None and is_first_user_turn(history):
        return True
    return False


@traceable(name="scope_gate", run_type="chain")
def scope_gate(
    message: str,
    *,
    prior_assistant: str | None = None,
    prior_user: str | None = None,
    bypass: bool = False,
    bypass_reason: str | None = None,
) -> dict:
    """Traced scope decision. Returns {verdict, reason} without changing gate logic."""
    if bypass:
        return {
            "verdict": "bypassed_pending_state",
            "reason": bypass_reason or "pending_state",
        }
    verdict = classify_scope(
        message,
        prior_assistant=prior_assistant,
        prior_user=prior_user,
    )
    return {"verdict": verdict, "reason": "classifier"}


def process_user_chat(
    graph,
    message: str,
    *,
    user_id: str,
    thread_id: str | None = None,
    endpoint: str = CHAT_ENDPOINT,
    image_base64: str | None = None,
    image_mime: str | None = None,
) -> dict:
    """Run defenses then the coaching team graph. Used by API and evals."""
    set_current_user_id(user_id)
    conversation = thread_id or str(uuid.uuid4())
    thread = make_thread_id(user_id, conversation)
    has_image = bool(image_base64 and image_base64.strip())
    normalized = normalize_user_message(message or "")
    if not normalized and not has_image:
        return {
            "thread_id": thread,
            "user_id": user_id,
            "reply": OUT_OF_SCOPE_REPLY,
            "coaching_team": {},
            "pending_approval": None,
            "quick_replies": [],
            "citations": [],
            "scope": "rejected_empty",
        }
    if not normalized and has_image:
        normalized = "Please look at this meal photo and log what I ate."

    profile = get_profile(user_id)
    config = thread_config(thread, user_id=user_id, endpoint=endpoint)
    pending = _pending_approval(graph, thread)
    history = _snapshot_messages(graph, thread)
    prior_assistant, prior_user = prior_turns_from_messages(history)
    first_turn = is_first_user_turn(history)
    pending_skip = should_skip_scope_gate(
        profile=profile, pending_approval=pending, history=None
    )

    def _enter_graph(*, bypass: bool, bypass_reason: str | None = None) -> dict:
        gate = scope_gate(
            normalized,
            prior_assistant=prior_assistant,
            prior_user=prior_user,
            bypass=bypass or has_image,
            bypass_reason=(
                "meal_photo" if has_image and not bypass
                else (bypass_reason or "pending_state")
            ),
        )
        result = graph.invoke(
            bootstrap_input(
                graph,
                thread,
                user_id=user_id,
                messages=[{"role": "user", "content": normalized}],
                pending_image_base64=image_base64 if has_image else None,
                pending_image_mime=(image_mime or "image/jpeg") if has_image else None,
            ),
            config=config,
        )
        payload = build_chat_payload(thread, result, graph=graph, config=config)
        payload["scope"] = gate["verdict"] if not has_image else "in_scope_meal_photo"
        payload["user_id"] = user_id
        return payload

    def _refuse(verdict: str) -> dict:
        log_out_of_scope(thread_id=thread, message=normalized, verdict=verdict)
        return {
            "thread_id": thread,
            "user_id": user_id,
            "reply": out_of_scope_reply(normalized),
            "coaching_team": {},
            "pending_approval": None,
            "quick_replies": [],
            "citations": [],
            "scope": verdict,
        }

    # ── 1) Plan-approval HITL resume (accept / reject / typed modify) ───────
    if pending and pending.get("type") == "plan_approval":
        gate = scope_gate(
            normalized,
            prior_assistant=prior_assistant,
            prior_user=prior_user,
            bypass=True,
            bypass_reason="plan_approval",
        )
        verdict = gate["verdict"]
        if looks_like_short_affirmation(normalized):
            from app.graph.approval_copy import approve_decision_reply

            is_first = bool(pending.get("is_first_plan"))
            result = graph.invoke(Command(resume="accept"), config=config)
            persist_approved_plan(graph, thread, user_id)
            payload = build_chat_payload(thread, result, graph=graph, config=config)
            payload["reply"] = approve_decision_reply("accept", is_first_plan=is_first)
            payload["pending_approval"] = None
            payload["coaching_team"] = {}
            payload["quick_replies"] = []
            payload["scope"] = verdict
            payload["user_id"] = user_id
            return payload
        if looks_like_short_reject(normalized):
            from app.graph.approval_copy import approve_decision_reply

            is_first = bool(pending.get("is_first_plan"))
            result = graph.invoke(Command(resume="reject"), config=config)
            payload = build_chat_payload(thread, result, graph=graph, config=config)
            payload["reply"] = approve_decision_reply("reject", is_first_plan=is_first)
            payload["pending_approval"] = None
            payload["coaching_team"] = {}
            payload["quick_replies"] = []
            payload["scope"] = verdict
            payload["user_id"] = user_id
            return payload
        # Free-text modification: clear the interrupt, keep the proposed draft as
        # the working week_plan, then run a normal coaching turn so Scheduler can
        # apply the tweak and (usually) interrupt again with an updated card.
        graph.invoke(Command(resume="modify"), config=config)
        return _enter_graph(bypass=True, bypass_reason="plan_approval_modify")

    # ── 2) First-turn bypass (empty checkpointer history) ───────────────────
    # UI greeting is client-only — never rely on it. Skip firm gating and route
    # to Coach/Intake, but still refuse clear off-topic / injection asks so the
    # bypass is not a hole (including when intake would also skip).
    # Meal photos are always in-scope nutrition — never gate them as OOS.
    if has_image:
        return _enter_graph(bypass=True, bypass_reason="meal_photo")

    if first_turn:
        # Welcome is client-only — feed it as prior so adherence openers that
        # answer "what got in the way this week" are not false-refused.
        oos_check = classify_scope(
            normalized,
            prior_assistant=prior_assistant or UI_WELCOME_PRIOR,
            prior_user=prior_user,
        )
        if oos_check == "out_of_scope":
            return _refuse(oos_check)
        # Complete-profile cold affirmations → gentle clarify (do not enter graph).
        # Incomplete intake still enters graph so Coach can ask for the goal.
        if (
            not pending_skip
            and looks_like_short_affirmation(normalized)
            and not looks_like_fitness_query(normalized)
        ):
            return {
                "thread_id": thread,
                "user_id": user_id,
                "reply": gentle_clarification_reply(),
                "coaching_team": {},
                "pending_approval": None,
                "quick_replies": ["my plan", "food", "a workout"],
                "citations": [],
                "scope": "gentle_clarify",
            }
        return _enter_graph(bypass=True, bypass_reason="first_user_turn")

    # ── 3) Intake / onboarding-confirm bypass ──────────────────────────────
    if pending_skip:
        return _enter_graph(bypass=True, bypass_reason="intake_pending")

    # ── 4) Context-aware scope gate ────────────────────────────────────────
    gate = scope_gate(
        normalized,
        prior_assistant=prior_assistant,
        prior_user=prior_user,
        bypass=False,
    )
    verdict = gate["verdict"]

    # Cold thread + vague affirmation → gentle clarify (do not firm-refuse)
    if (
        verdict == "in_scope"
        and not (prior_assistant or "").strip()
        and looks_like_short_affirmation(normalized)
        and not looks_like_fitness_query(normalized)
    ):
        return {
            "thread_id": thread,
            "user_id": user_id,
            "reply": gentle_clarification_reply(),
            "coaching_team": {},
            "pending_approval": None,
            "quick_replies": ["my plan", "food", "a workout"],
            "citations": [],
            "scope": "gentle_clarify",
        }

    if verdict == "out_of_scope":
        return _refuse(verdict)

    return _enter_graph(bypass=False)

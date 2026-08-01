"""Load profile and plan context into graph state; persist approved plans."""
import logging
from typing import Any

from app.graph.runtime import thread_config, user_id_from_thread
from app.graph.state import CoachingTeamState, WeekPlan
from app.memory.store import (
    get_adherence_stats,
    get_profile,
    get_saved_week_plan,
    get_week_workout_logs,
    save_week_plan,
)
from app.memory.user_context import set_current_user_id

logger = logging.getLogger("steadyfit.plan")


def _coerce_week_plan(raw: Any) -> WeekPlan | None:
    if raw is None:
        return None
    if isinstance(raw, WeekPlan):
        return raw
    if isinstance(raw, dict):
        try:
            return WeekPlan(**raw)
        except (TypeError, ValueError):
            return None
    return None


def week_plan_from_graph(graph, thread_id: str) -> WeekPlan | None:
    try:
        snapshot = graph.get_state(thread_config(thread_id))
    except Exception:
        return None
    if not snapshot or not snapshot.values:
        return None
    values = snapshot.values
    raw = values.get("week_plan") if isinstance(values, dict) else getattr(values, "week_plan", None)
    return _coerce_week_plan(raw)


def bootstrap_input(
    graph,
    thread_id: str,
    *,
    user_id: str,
    messages: list | None = None,
    retrieved_context: list[str] | None = None,
    pending_image_base64: str | None = None,
    pending_image_mime: str | None = None,
) -> CoachingTeamState:
    """Merge long-term memory into each graph invoke."""
    set_current_user_id(user_id)
    profile = get_profile(user_id)
    week_plan = week_plan_from_graph(graph, thread_id) or get_saved_week_plan(user_id)

    # Carry Memory chunks/citations from the prior turn so adherence →
    # "yes schedule" continuations keep the same grounding (capped).
    prior_ctx: list[str] = []
    prior_cites: list[dict] = []
    try:
        snapshot = graph.get_state(thread_config(thread_id))
        values = getattr(snapshot, "values", None) if snapshot else None
        if isinstance(values, dict):
            raw_ctx = values.get("retrieved_context") or []
            raw_cites = values.get("citations") or []
            prior_ctx = [
                c for c in raw_ctx
                if isinstance(c, str) and "[Memory:" in c
            ][-3:]
            prior_cites = [
                c for c in raw_cites
                if isinstance(c, dict)
                and (
                    str(c.get("kind") or "").lower() == "memory"
                    or str(c.get("tag") or "").startswith("[Memory:")
                )
            ][-6:]
    except Exception:
        pass

    ctx = list(retrieved_context) if retrieved_context is not None else list(prior_ctx)
    if retrieved_context is not None and prior_ctx:
        for chunk in prior_ctx:
            if chunk not in ctx:
                ctx.append(chunk)

    return CoachingTeamState(
        messages=messages or [],
        user_id=user_id,
        profile=profile,
        week_plan=week_plan,
        retrieved_context=ctx,
        citations=prior_cites,
        pending_image_base64=pending_image_base64,
        pending_image_mime=pending_image_mime,
    )


def persist_approved_plan(graph, thread_id: str, user_id: str | None = None):
    """Write the thread's approved week plan to long-term memory."""
    uid = user_id or user_id_from_thread(thread_id)
    if not uid:
        return
    plan = week_plan_from_graph(graph, thread_id)
    if plan and plan.days:
        save_week_plan(uid, plan)
        return
    logger.warning(
        "persist_approved_plan: no week_plan with days for user=%s thread=%s",
        uid,
        thread_id,
    )


def plan_snapshot(graph, thread_id: str, user_id: str) -> dict:
    """API payload for the /plan view."""
    set_current_user_id(user_id)
    profile = get_profile(user_id)
    week_plan = week_plan_from_graph(graph, thread_id) or get_saved_week_plan(user_id)
    profile_data = profile.model_dump()
    profile_data["injuries"] = profile.injuries
    profile_data["food_preferences"] = profile.food_preferences
    profile_data["workout_preferences"] = profile.workout_preferences
    week_start = week_plan.week_start if week_plan else None
    return {
        "thread_id": thread_id,
        "user_id": user_id,
        "profile": profile_data,
        "week_plan": week_plan.model_dump() if week_plan else None,
        "adherence": get_adherence_stats(user_id),
        "workout_logs": get_week_workout_logs(user_id, week_start),
    }

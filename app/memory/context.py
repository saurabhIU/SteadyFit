"""Load profile and plan context into graph state; persist approved plans."""
from typing import Any

from app.graph.runtime import thread_config
from app.graph.state import CoachingTeamState, UserProfile, WeekPlan
from app.memory.store import get_adherence_stats, get_profile, get_saved_week_plan, save_week_plan


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
    snapshot = graph.get_state(thread_config(thread_id))
    if not snapshot or not snapshot.values:
        return None
    values = snapshot.values
    raw = values.get("week_plan") if isinstance(values, dict) else getattr(values, "week_plan", None)
    return _coerce_week_plan(raw)


def bootstrap_input(
    graph,
    thread_id: str,
    *,
    messages: list | None = None,
) -> CoachingTeamState:
    """Merge long-term memory into each graph invoke."""
    profile = get_profile()
    week_plan = week_plan_from_graph(graph, thread_id) or get_saved_week_plan()
    return CoachingTeamState(
        messages=messages or [],
        profile=profile,
        week_plan=week_plan,
    )


def persist_approved_plan(graph, thread_id: str):
    """Write the thread's approved week plan to SQLite long-term memory."""
    plan = week_plan_from_graph(graph, thread_id)
    if plan:
        save_week_plan(plan)


def plan_snapshot(graph, thread_id: str) -> dict:
    """API payload for the /plan view."""
    profile = get_profile()
    week_plan = week_plan_from_graph(graph, thread_id) or get_saved_week_plan()
    return {
        "thread_id": thread_id,
        "profile": profile.model_dump(),
        "week_plan": week_plan.model_dump() if week_plan else None,
        "adherence": get_adherence_stats(),
    }

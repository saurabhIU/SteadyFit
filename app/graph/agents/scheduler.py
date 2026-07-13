"""Scheduler agent: life-aware weekly re-planning."""
from app.config import get_llm
from app.graph.plan_utils import parse_week_plan
from app.graph.state import CoachingTeamState
from app.tools.calendar_tool import get_calendar_conflicts

SYSTEM = """You are the Scheduler agent. The user is a busy everyday person.
Given their profile, current week plan, and calendar conflicts, propose a realistic
re-planned week. Prefer moving sessions over dropping them; prefer shorter sessions
over skipped ones; never stack hard sessions on consecutive low-recovery days.

Write a short warm proposal, then end with a fenced JSON block for the updated plan:
```json
{
  "week_start": "2026-07-14",
  "days": [{"day": "Mon", "focus": "Upper push", "duration_min": 45, "status": "planned"}],
  "calorie_target": 2200,
  "protein_target_g": 150,
  "notes": "optional"
}
```"""


def scheduler_node(state: CoachingTeamState) -> dict:
    conflicts = get_calendar_conflicts()
    llm = get_llm()
    prompt = (
        f"Profile: {state.profile.model_dump_json()}\n"
        f"Plan: {state.week_plan.model_dump_json() if state.week_plan else 'none'}\n"
        f"Calendar conflicts: {conflicts}\n"
        f"User request: {state.messages[-1].content if state.messages else ''}"
    )
    proposal = llm.invoke([{"role": "system", "content": SYSTEM},
                           {"role": "user", "content": prompt}]).content
    parsed = parse_week_plan(proposal)
    proposals = {**state.proposals, "scheduler": proposal, "plan_changed": True}
    if parsed:
        proposals["proposed_week_plan"] = parsed.model_dump()
    return {"proposals": proposals}

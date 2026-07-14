"""Scheduler agent: life-aware weekly re-planning (agentic calendar tool calling)."""
from app.graph.plan_utils import parse_week_plan
from app.graph.state import CoachingTeamState
from app.graph.tool_agent import run_tool_agent
from app.security import as_text, with_security, wrap_untrusted
from app.tools.agent_tools import SCHEDULER_TOOLS

SYSTEM = """You are the Scheduler agent. The user is a busy everyday person.
Use the calendar_conflicts tool to learn their busy blocks before proposing changes.
Prefer moving sessions over dropping them; prefer shorter sessions over skipped ones;
never stack hard sessions on consecutive low-recovery days.

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
    user_msg = as_text(state.messages[-1].content) if state.messages else ""
    first_plan = (
        state.intent == "first_plan"
        or state.proposals.get("intake_handoff") == "first_plan"
        or state.week_plan is None
    )
    hint = (
        "This is their FIRST week after onboarding. Build a realistic week that "
        "matches preferred_workout_modes and sessions_per_week. Align focus days "
        "with their modes (e.g. walking/gym). Set sensible calorie_target and "
        "protein_target_g for the stated goal and food_preference."
        if first_plan
        else "Call calendar_conflicts, then propose the re-planned week."
    )
    user_prompt = (
        f"Profile: {state.profile.model_dump_json()}\n"
        f"Plan: {state.week_plan.model_dump_json() if state.week_plan else 'none'}\n"
        f"{wrap_untrusted(user_msg, source='user')}\n\n"
        f"{hint}"
    )
    result = run_tool_agent(
        system=with_security(SYSTEM),
        user=user_prompt,
        tools=SCHEDULER_TOOLS,
    )
    proposal = result.text
    parsed = parse_week_plan(proposal)
    proposals = {**state.proposals, "scheduler": proposal, "plan_changed": True}
    if parsed:
        proposals["proposed_week_plan"] = parsed.model_dump()
    if result.tools_called:
        proposals["scheduler_tools"] = result.tools_called
    return {"proposals": proposals}

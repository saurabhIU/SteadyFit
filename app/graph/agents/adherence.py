"""Adherence agent: agentic stats tool calling; RISK → simplify plan."""
from app.graph.state import CoachingTeamState
from app.graph.tool_agent import run_tool_agent
from app.security import with_security, wrap_untrusted
from app.tools.agent_tools import ADHERENCE_TOOLS

SYSTEM = """You are the Adherence agent. Always call the adherence_stats tool first.
Inspect streaks, skips, and logging gaps. If the user shows drop-off signals
(e.g. 3+ skipped sessions in 10 days, no logs for 5+ days), recommend making
the plan EASIER. Warm, brief, never guilt-tripping.
Start your final reply with 'RISK' if risk is present; otherwise do not."""


def adherence_node(state: CoachingTeamState) -> dict:
    user_prompt = (
        f"Profile: {state.profile.model_dump_json()}\n"
        f"{wrap_untrusted('Check adherence and report.', source='system_hint')}\n\n"
        "Call adherence_stats, then give your assessment."
    )
    result = run_tool_agent(
        system=with_security(SYSTEM),
        user=user_prompt,
        tools=ADHERENCE_TOOLS,
    )
    proposal = result.text
    proposals = {**state.proposals, "adherence": proposal}
    if result.tools_called:
        proposals["adherence_tools"] = result.tools_called
    return {
        "proposals": proposals,
        "risk_flag": proposal.strip().upper().startswith("RISK"),
    }

"""Adherence agent: detects drop-off risk; asks the AI Coaching Team to SIMPLIFY, not push."""
from app.config import get_llm
from app.graph.state import CoachingTeamState
from app.memory.store import get_adherence_stats

SYSTEM = """You are the Adherence agent. Inspect adherence stats (streaks, skips,
logging gaps). If the user shows drop-off signals (e.g. 3+ skipped sessions in 10 days,
no logs for 5+ days), set RISK and recommend making the plan EASIER. Warm, brief,
never guilt-tripping. Start your reply with 'RISK' if risk is present."""


def adherence_node(state: CoachingTeamState) -> dict:
    stats = get_adherence_stats()
    llm = get_llm()
    proposal = llm.invoke([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Stats: {stats}\nProfile: {state.profile.model_dump_json()}"},
    ]).content
    return {
        "proposals": {**state.proposals, "adherence": proposal},
        "risk_flag": proposal.strip().upper().startswith("RISK"),
    }

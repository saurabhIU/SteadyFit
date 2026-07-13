"""Adherence agent: detects drop-off risk; asks the AI Coaching Team to SIMPLIFY, not push."""
from app.config import get_llm
from app.graph.state import CoachingTeamState
from app.memory.store import get_adherence_stats
from app.security import as_text, with_security, wrap_untrusted

SYSTEM = """You are the Adherence agent. Inspect adherence stats (streaks, skips,
logging gaps). If the user shows drop-off signals (e.g. 3+ skipped sessions in 10 days,
no logs for 5+ days), set RISK and recommend making the plan EASIER. Warm, brief,
never guilt-tripping. Start your reply with 'RISK' if risk is present."""


def adherence_node(state: CoachingTeamState) -> dict:
    stats = get_adherence_stats()
    llm = get_llm()
    proposal = as_text(llm.invoke([
        {"role": "system", "content": with_security(SYSTEM)},
        {
            "role": "user",
            "content": (
                f"{wrap_untrusted(str(stats), source='adherence_stats')}\n"
                f"Profile: {state.profile.model_dump_json()}"
            ),
        },
    ]).content)
    return {
        "proposals": {**state.proposals, "adherence": proposal},
        "risk_flag": proposal.strip().upper().startswith("RISK"),
    }

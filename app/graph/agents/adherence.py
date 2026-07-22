"""Adherence agent: agentic stats tool calling; RISK → simplify plan."""
from app.graph.citations import citations_from_texts, merge_citations
from app.graph.critique import revision_block
from app.graph.state import CoachingTeamState
from app.graph.tool_agent import run_tool_agent
from app.rag.memory_store import retrieve_memories
from app.security import as_text, with_security, wrap_untrusted
from app.tools.agent_tools import ADHERENCE_TOOLS

SYSTEM = """You are the Adherence agent. Always call the adherence_stats tool first.
Inspect streaks, skips, and logging gaps. If the user shows drop-off signals
(e.g. 3+ skipped sessions in 10 days, no logs for 5+ days), recommend making
the plan EASIER. Warm, brief, never guilt-tripping.
If past-week Memory blocks appear, you may cite them with [Memory: week of YYYY-MM-DD]
when they show a prior successful simplification — never moralize using memory.
Start your final reply with 'RISK' if risk is present; otherwise do not."""


def adherence_node(state: CoachingTeamState) -> dict:
    user_msg = as_text(state.messages[-1].content) if state.messages else ""
    memory_chunks, memory_cites = retrieve_memories(
        f"{user_msg}\nsimplified plan overload stress adherence",
        user_id=state.user_id,
        k=3,
    )
    memory_block = "\n\n".join(memory_chunks) if memory_chunks else ""
    user_prompt = (
        f"Profile: {state.profile.model_dump_json()}\n"
        f"{wrap_untrusted(user_msg or 'Check adherence and report.', source='user')}\n\n"
        f"{memory_block}\n\n"
        "Call adherence_stats, then give your assessment."
        f"{revision_block(state)}"
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
    cites = merge_citations(
        list(state.citations),
        memory_cites,
        citations_from_texts([proposal] + memory_chunks),
    )
    return {
        "proposals": proposals,
        "risk_flag": proposal.strip().upper().startswith("RISK"),
        "retrieved_context": state.retrieved_context + memory_chunks,
        "citations": cites,
    }

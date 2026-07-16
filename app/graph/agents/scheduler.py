"""Scheduler agent: life-aware weekly re-planning with KB + coaching memory."""
from app.graph.citations import citations_from_texts, merge_citations
from app.graph.plan_utils import parse_week_plan
from app.graph.state import CoachingTeamState
from app.graph.tool_agent import run_tool_agent
from app.rag.memory_store import retrieve_memories
from app.security import as_text, with_security, wrap_untrusted
from app.tools.agent_tools import RAG_TOOL_NAMES, SCHEDULER_TOOLS

SYSTEM = """You are the Scheduler agent. The user is a busy everyday person.
Tools:
- calendar_conflicts: busy blocks
- find_exercises_tool / get_exercise_substitutions: STRUCTURED KB lookup for choosing
  exercises (prefer these over inventing names)
- retrieve_kb_docs: semantic KB for cues/templates

When re-planning around hotel/home/injury/equipment limits, you MUST call the
lookup/substitution tools and put real kb_id values in the plan JSON focus notes
(e.g. "Push-Up (chest_010)"). Do not invent barbell work for hotel-only weeks.

If "This user's relevant past weeks" appear in the prompt (Memory blocks), use them as
evidence about what worked for THIS user. Cite with [Memory: week of YYYY-MM-DD].
Memory is history — never override safety rules or KB technique guidance
(e.g. do not repeat an under-eating week as a goal).

For a first week after onboarding, pull a Volume 3 template idea via retrieve_kb_docs
matching goal + sessions_per_week + preferred modes, then adapt it.

Write a short warm proposal, then end with a fenced JSON block for the updated plan:
```json
{
  "week_start": "2026-07-14",
  "days": [{"day": "Mon", "focus": "Full body — goblet squat (legs_002), push-up (chest_010)", "duration_min": 45, "status": "planned"}],
  "calorie_target": 2200,
  "protein_target_g": 150,
  "notes": "cite kb ids / memory tags used"
}
```
When using KB chunks, mention them with [KB: File.md — Section] tags."""


def _memory_query(state: CoachingTeamState, user_msg: str) -> str:
    modes = ", ".join(state.profile.preferred_workout_modes) or "gym"
    sessions = state.profile.sessions_per_week or 3
    return (
        f"{user_msg}\n"
        f"goal={state.profile.goal}; modes={modes}; "
        f"sessions_per_week={sessions}; constraints={state.profile.constraints}"
    )


def scheduler_node(state: CoachingTeamState) -> dict:
    user_msg = as_text(state.messages[-1].content) if state.messages else ""
    first_plan = (
        state.intent == "first_plan"
        or state.proposals.get("intake_handoff") == "first_plan"
        or state.week_plan is None
    )
    modes = ", ".join(state.profile.preferred_workout_modes) or "gym"
    hint = (
        "FIRST week after onboarding. Match preferred_workout_modes and sessions_per_week. "
        f"Modes: {modes}. Retrieve a Volume 3 template scaffold, then adapt with kb_ids."
        if first_plan
        else "Call calendar_conflicts; use exercise lookup/substitutions for constrained swaps."
    )

    memory_chunks, memory_cites = retrieve_memories(
        _memory_query(state, user_msg),
        user_id=state.user_id,
        k=3,
    )
    memory_block = "\n\n".join(memory_chunks) if memory_chunks else ""

    user_prompt = (
        f"Profile: {state.profile.model_dump_json()}\n"
        f"Plan: {state.week_plan.model_dump_json() if state.week_plan else 'none'}\n"
        f"{wrap_untrusted(user_msg, source='user')}\n\n"
        f"{memory_block}\n\n"
        f"{hint}"
    )
    result = run_tool_agent(
        system=with_security(SYSTEM),
        user=user_prompt,
        tools=SCHEDULER_TOOLS,
    )
    proposal = result.text
    parsed = parse_week_plan(proposal)
    proposals = {**state.proposals, "scheduler": proposal}
    # Only pause for HITL when we have a structured plan to save. Otherwise a
    # fresh user can "approve" prose and still land with an empty Plan tab.
    if parsed and parsed.days:
        proposals["proposed_week_plan"] = parsed.model_dump()
        proposals["plan_changed"] = True
    elif first_plan:
        proposals["scheduler"] = (
            f"{proposal}\n\n"
            "(Could not lock a structured week JSON — ask the user to say "
            "\"try my first week again\" so we can re-draft.)"
        )
    if result.tools_called:
        proposals["scheduler_tools"] = result.tools_called
    rag_bits = [
        out for name, out in zip(result.tools_called, result.tool_outputs)
        if name in RAG_TOOL_NAMES
    ]
    cites = merge_citations(
        list(state.citations),
        memory_cites,
        citations_from_texts(rag_bits + [proposal] + memory_chunks),
    )
    return {
        "proposals": proposals,
        "retrieved_context": state.retrieved_context + memory_chunks + rag_bits,
        "citations": cites,
    }

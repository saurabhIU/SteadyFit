"""Scheduler agent: life-aware weekly re-planning with KB + coaching memory."""
from app.graph.citations import citations_from_texts, merge_citations
from app.graph.critique import revision_block
from app.graph.macros import PROVISIONAL_MACRO_INSTRUCTIONS, macros_provisional
from app.graph.plan_utils import parse_week_plan
from app.graph.state import CoachingTeamState
from app.graph.tool_agent import run_tool_agent
from app.rag.memory_store import retrieve_memories
from app.security import (
    as_text,
    looks_like_pain_injury_interrupt,
    with_security,
    wrap_untrusted,
)
from app.tools.agent_tools import RAG_TOOL_NAMES, SCHEDULER_TOOLS

SYSTEM = """You are the Scheduler agent. The user is a busy everyday person.
Tools:
- calendar_conflicts: real busy blocks only (often empty until Calendar OAuth)
- find_exercises_tool / get_exercise_substitutions: STRUCTURED KB lookup for choosing
  exercises (prefer these over inventing names)
- retrieve_kb_docs: semantic KB for cues/templates

CALENDAR / TRAVEL (CRITICAL):
- You may ONLY reference travel, meetings, flights, or busy blocks that the USER
  EXPLICITLY stated in this conversation or listed in their profile constraints.
- An empty calendar_conflicts result means ZERO known conflicts — do not invent
  travel, "client site" flights, hotel weeks, or meetings.
- Never treat a mock, demo, or empty calendar tool result as evidence of a real
  scheduling constraint.

When re-planning around hotel/home/injury/equipment limits the USER stated, you MUST
call the lookup/substitution tools and put real kb_id values in the plan JSON focus
notes (e.g. "Push-Up (chest_010)"). Do not invent barbell work for hotel-only weeks.

For pain/injury interrupts (knee, shoulder, etc.): acknowledge the concern first,
pull knee-/joint-safe substitutions from the KB, and do NOT continue an unrelated
prior nutrition thread. Never encourage training through sharp pain.

If "This user's relevant past weeks" appear in the prompt (Memory blocks), use them as
evidence about what worked for THIS user. Cite with [Memory: week of YYYY-MM-DD].
Memory is history — never override safety rules or KB technique guidance
(e.g. do not repeat an under-eating week as a goal). Never invent travel from memory
unless that memory clearly belongs to THIS user's stated history AND the user asked
about a similar situation.

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
When stating calorie_target / protein_target_g without profile weight_kg, treat them as
starting estimates — put the provisional caveat INLINE next to any numbers you write
in prose, and ask for current weight in the same proposal.
When using KB chunks, mention them with [KB: File.md — Section] tags.

Do NOT tell the user to "reply approve" or type a confirmation keyword — the UI
approval card handles plan confirmation."""


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
    if first_plan:
        hint = (
            "FIRST week after onboarding. Match preferred_workout_modes and sessions_per_week. "
            f"Modes: {modes}. Retrieve a Volume 3 template scaffold, then adapt with kb_ids. "
            "Do NOT invent travel/meetings — calendar is empty unless the user stated conflicts."
        )
    elif looks_like_pain_injury_interrupt(user_msg):
        hint = (
            "PAIN/INJURY INTERRUPT: acknowledge the joint/pain concern first. "
            "Call get_exercise_substitutions / find_exercises_tool for safer options. "
            "Propose knee-safe (or relevant joint-safe) swaps; do not push through pain. "
            "Do not discuss protein/meal plans."
        )
    else:
        hint = (
            "Call calendar_conflicts only as a check; if empty, schedule from the user's "
            "stated constraints only. Use exercise lookup/substitutions for constrained swaps."
        )
    if macros_provisional(state.profile):
        hint = f"{hint}\n\n{PROVISIONAL_MACRO_INSTRUCTIONS}"

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
        f"{revision_block(state)}"
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

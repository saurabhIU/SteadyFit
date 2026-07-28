"""Scheduler agent: life-aware weekly re-planning with KB + coaching memory."""
from app.graph.citations import citations_from_texts, merge_citations
from app.graph.critique import revision_block
from app.graph.diet_plan import build_diet_week, diet_plan_contains_nonveg, diet_summary_lines
from app.graph.macros import (
    PROVISIONAL_MACRO_INSTRUCTIONS,
    has_body_stats,
    macros_provisional,
)
from app.graph.micro_workout import (
    DONE_CHIP,
    build_ten_minute_reply,
    handle_quick_10_choice,
    handle_quick_10_done,
    looks_like_ten_minute_request,
)
from app.graph.plan_utils import current_week_start_iso, parse_week_plan
from app.graph.state import CoachingTeamState
from app.graph.tdee import compute_macro_targets
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
  "week_start": "YYYY-MM-DD",
  "days": [{"day": "Mon", "focus": "Full body — goblet squat (legs_002), push-up (chest_010)", "duration_min": 45, "status": "planned"}],
  "calorie_target": 2200,
  "protein_target_g": 150,
  "notes": "cite kb ids / memory tags used"
}
```
IMPORTANT: week_start will be overwritten in code to this calendar week's Monday —
you may put any ISO date; do not invent a far-past or far-future week for display.

When stating calorie_target / protein_target_g without profile weight_kg, treat them as
starting estimates — put the provisional caveat INLINE next to any numbers you write
in prose. Do NOT ask for weight in this proposal (weight was already declined or the
weight gate handles that in a separate turn).
When profile has weight_kg, ground calorie/protein in that weight — no "estimate" or
"share your weight" framing.
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
    last = state.messages[-1] if state.messages else None
    if last is None:
        user_msg = ""
    elif hasattr(last, "content"):
        user_msg = as_text(last.content)
    elif isinstance(last, dict):
        user_msg = as_text(last.get("content", ""))
    else:
        user_msg = as_text(str(last))

    # Quick-10 Done / replace / extra — before suggestion path.
    choice = state.proposals.get("micro_done_choice")
    if choice in {"replace", "extra"}:
        result = handle_quick_10_choice(
            user_id=state.user_id or "",
            profile=state.profile,
            week_plan=state.week_plan,
            choice=choice,  # type: ignore[arg-type]
        )
        out: dict = {
            "proposals": {
                "scheduler": result.reply,
                "micro_session_log": True,
                "plan_changed": False,
                "awaiting_quick_10_choice": False,
                "quick_replies": result.quick_replies,
            },
            "retrieved_context": state.retrieved_context,
            "citations": list(state.citations),
        }
        if result.week_plan is not None:
            out["week_plan"] = result.week_plan
        return out

    if state.proposals.get("micro_done"):
        result = handle_quick_10_done(
            user_id=state.user_id or "",
            profile=state.profile,
            week_plan=state.week_plan,
        )
        return {
            "proposals": {
                "scheduler": result.reply,
                "micro_session_log": True,
                "plan_changed": False,
                "awaiting_quick_10_choice": result.awaiting_choice,
                "quick_replies": result.quick_replies,
            },
            "retrieved_context": state.retrieved_context,
            "citations": list(state.citations),
        }

    # Instant 10-minute session — no LLM, no week-plan HITL.
    if state.proposals.get("micro_session") or looks_like_ten_minute_request(user_msg):
        reply = build_ten_minute_reply(state.profile)
        return {
            "proposals": {
                **state.proposals,
                "scheduler": reply,
                "micro_session": True,
                "plan_changed": False,
            },
            "retrieved_context": state.retrieved_context,
            "citations": list(state.citations),
        }

    first_plan = (
        state.intent == "first_plan"
        or state.proposals.get("intake_handoff") == "first_plan"
        or state.week_plan is None
    )
    modes = ", ".join(state.profile.preferred_workout_modes) or "gym"
    week_start = current_week_start_iso()
    if first_plan:
        hint = (
            "FIRST week after onboarding. Match preferred_workout_modes and sessions_per_week. "
            f"Modes: {modes}. Retrieve a Volume 3 template scaffold, then adapt with kb_ids. "
            "Do NOT invent travel/meetings — calendar is empty unless the user stated conflicts. "
            f"Use week_start={week_start} (this week's Monday) in the JSON."
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

    macro_targets = compute_macro_targets(
        weight_kg=state.profile.weight_kg,
        height_cm=state.profile.height_cm,
        age=state.profile.age,
        sex=state.profile.sex,
        activity_level=state.profile.activity_level,  # type: ignore[arg-type]
        target_weight_kg=state.profile.target_weight_kg,
        goal=state.profile.goal,
    )
    hint = (
        f"{hint}\n\nCODE-COMPUTED MACRO TARGETS (Mifflin-St Jeor — use these exact numbers "
        f"in calorie_target / protein_target_g JSON fields; do not invent different ones): "
        f"calorie_target={macro_targets.calorie_target}, "
        f"protein_target_g={macro_targets.protein_target_g}, "
        f"tdee={macro_targets.tdee_kcal}, is_estimate={macro_targets.is_estimate}.\n"
    )
    if macro_targets.is_estimate or macros_provisional(state.profile):
        hint = f"{hint}\n{PROVISIONAL_MACRO_INSTRUCTIONS}\n"
    elif has_body_stats(state.profile):
        hint = (
            f"{hint}\nWEIGHT/HEIGHT known — present targets as computed, not guesses. "
            "Do NOT ask for weight again.\n"
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
        # Authoritative week_start = this calendar week's Monday (never LLM placeholder).
        parsed.week_start = week_start
        # Override LLM macros with code-computed TDEE (daily-totals principle).
        parsed.calorie_target = macro_targets.calorie_target
        parsed.protein_target_g = macro_targets.protein_target_g
        if macro_targets.is_estimate:
            note = (parsed.notes or "").strip()
            caveat = "Macros are starting estimates (incomplete body stats)."
            parsed.notes = f"{note} {caveat}".strip()
        proposals["proposed_week_plan"] = parsed.model_dump()
        proposals["plan_changed"] = True
        proposals["tdee_targets"] = {
            "calorie_target": macro_targets.calorie_target,
            "protein_target_g": macro_targets.protein_target_g,
            "tdee_kcal": macro_targets.tdee_kcal,
            "bmr_kcal": macro_targets.bmr_kcal,
            "is_estimate": macro_targets.is_estimate,
            "formula": macro_targets.formula,
            "notes": macro_targets.notes,
        }
        diet_meals = build_diet_week(
            state.profile,
            week_start=week_start,
            conversation_text=user_msg,
        )
        # Preference safety: never ship non-veg to vegetarian/vegan profiles.
        pref = (state.profile.food_preference or "").lower()
        if pref in {"vegetarian", "vegan", "eggetarian"} and diet_plan_contains_nonveg(diet_meals):
            safe_pref = "vegan" if pref == "vegan" else "vegetarian"
            diet_meals = build_diet_week(
                state.profile.model_copy(update={"food_preference": safe_pref}),
                week_start=week_start,
                conversation_text=user_msg,
            )
        proposals["proposed_diet_plan"] = diet_meals
        proposals["diet_plan_summary"] = diet_summary_lines(diet_meals)
        proposals["nutrition_plan_change"] = True
        # Keep scheduler draft short for any downstream LLM — day detail lives in
        # proposed_week_plan / proposed_diet_plan (approval card source of truth).
        proposals["scheduler"] = (
            f"{proposal}\n\n"
            f"[structured week_start={week_start}; "
            f"{len(parsed.days)} workout days; {len(diet_meals)} planned meals]"
        )
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

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
from app.graph.personalization import (
    apply_personalization_flags,
    load_personal_plan_context,
    scrub_diet_for_food_avoids,
    scrub_week_plan_for_avoids,
)
from app.graph.plan_utils import current_week_start_iso, parse_week_plan
from app.graph.state import CoachingTeamState, WeekPlan, WorkoutDay
from app.graph.tdee import compute_macro_targets
from app.graph.tool_agent import run_tool_agent
from app.graph.weight_gate import (
    looks_like_first_plan_request,
    looks_like_training_day_preference,
)
from app.memory.store import get_saved_week_plan
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
approval card handles plan confirmation.

CRITICAL OUTPUT RULE: When drafting or rebuilding a week (first plan, personal-doc
apply, or weekday preference), you MUST end with the fenced WeekPlan JSON above.
Do not ask "sound good?" or defer meals to a later turn — include workouts in JSON
now; meals are attached in code."""


def _fallback_week_plan(
    state: CoachingTeamState,
    *,
    week_start: str,
    calorie_target: int,
    protein_target_g: int,
) -> WeekPlan:
    """Deterministic scaffold when the LLM omits parseable WeekPlan JSON."""
    base = state.week_plan
    if base is None and state.user_id:
        base = get_saved_week_plan(state.user_id)
    if base and base.days:
        days = [
            d.model_copy(update={"status": "planned"})
            for d in base.days
        ]
        return WeekPlan(
            week_start=week_start,
            days=days,
            calorie_target=calorie_target,
            protein_target_g=protein_target_g,
            notes=(base.notes or "").strip()
            or "Rebuilt from your current week (structured fallback).",
        )
    sessions = max(3, min(4, int(state.profile.sessions_per_week or 3)))
    # Prefer Mon/Wed/Sat (+Tue if 4) — leave Friday free by default.
    foci = [
        ("Monday", "Full body — goblet squat, push-up, row"),
        ("Wednesday", "Upper — incline press, lat pulldown, core"),
        ("Saturday", "Lower — leg press, Romanian deadlift, hinge pattern"),
        ("Tuesday", "Full body — lighter accessories + walk"),
    ]
    days = [
        WorkoutDay(day=name, focus=focus, duration_min=45, status="planned")
        for name, focus in foci[:sessions]
    ]
    for rest in ("Thursday", "Friday", "Sunday"):
        if not any(d.day == rest for d in days):
            days.append(
                WorkoutDay(day=rest, focus="Rest", duration_min=0, status="planned")
            )
    return WeekPlan(
        week_start=week_start,
        days=days,
        calorie_target=calorie_target,
        protein_target_g=protein_target_g,
        notes="Structured fallback week (3–4 sessions; Friday rest).",
    )


def _attach_structured_plan(
    *,
    proposals: dict,
    parsed: WeekPlan,
    week_start: str,
    macro_targets,
    personal_ctx,
    state: CoachingTeamState,
    user_msg: str,
    proposal: str,
) -> dict:
    """Finalize plan_changed proposals + diet + personalization flags."""
    parsed.week_start = week_start
    parsed.calorie_target = macro_targets.calorie_target
    parsed.protein_target_g = macro_targets.protein_target_g
    if macro_targets.is_estimate:
        note = (parsed.notes or "").strip()
        caveat = "Macros are starting estimates (incomplete body stats)."
        parsed.notes = f"{note} {caveat}".strip()
    doc_tag = None
    if personal_ctx.citations:
        doc_tag = personal_ctx.citations[0].get("tag")
    if personal_ctx.avoid_terms:
        parsed = scrub_week_plan_for_avoids(
            parsed, personal_ctx.avoid_terms, source_tag=doc_tag
        )
    proposals["proposed_week_plan"] = parsed.model_dump()
    proposals["plan_changed"] = True
    proposals = apply_personalization_flags(proposals, personal_ctx)
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
    pref = (state.profile.food_preference or "").lower()
    if pref in {"vegetarian", "vegan", "eggetarian"} and diet_plan_contains_nonveg(
        diet_meals
    ):
        safe_pref = "vegan" if pref == "vegan" else "vegetarian"
        diet_meals = build_diet_week(
            state.profile.model_copy(update={"food_preference": safe_pref}),
            week_start=week_start,
            conversation_text=user_msg,
        )
    if personal_ctx.food_avoids:
        diet_meals = scrub_diet_for_food_avoids(
            diet_meals, personal_ctx.food_avoids, source_tag=doc_tag
        )
    proposals["proposed_diet_plan"] = diet_meals
    proposals["diet_plan_summary"] = diet_summary_lines(diet_meals)
    proposals["nutrition_plan_change"] = True
    proposals["scheduler"] = (
        f"{proposal}\n\n"
        f"[structured week_start={week_start}; "
        f"{len(parsed.days)} workout days; {len(diet_meals)} planned meals]"
    )
    return proposals


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
            "stated constraints only. Use exercise lookup/substitutions for constrained swaps. "
            "If the user asked to skip/prefer certain weekdays or rebuild the week, "
            "ALWAYS emit a full WeekPlan JSON (plan_changed) — never advisory-only."
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

    personal_ctx = load_personal_plan_context(state.user_id or "", state.profile)
    personal_block = personal_ctx.prompt_block
    if personal_block:
        personal_block = f"\n{personal_block}\n"

    user_prompt = (
        f"Profile: {state.profile.model_dump_json()}\n"
        f"Plan: {state.week_plan.model_dump_json() if state.week_plan else 'none'}\n"
        f"{wrap_untrusted(user_msg, source='user')}\n\n"
        f"{memory_block}\n"
        f"{personal_block}"
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
    must_structure = (
        first_plan
        or looks_like_first_plan_request(user_msg)
        or looks_like_training_day_preference(user_msg)
    )
    # Only pause for HITL when we have a structured plan to save. Otherwise a
    # fresh user can "approve" prose and still land with an empty Plan tab.
    if parsed and parsed.days:
        proposals = _attach_structured_plan(
            proposals=proposals,
            parsed=parsed,
            week_start=week_start,
            macro_targets=macro_targets,
            personal_ctx=personal_ctx,
            state=state,
            user_msg=user_msg,
            proposal=proposal,
        )
    elif must_structure:
        # LLM wrote an essay instead of JSON — still ship a HITL card so
        # personalization/rebuild never dies as chat-only advice.
        fallback = _fallback_week_plan(
            state,
            week_start=week_start,
            calorie_target=macro_targets.calorie_target,
            protein_target_g=macro_targets.protein_target_g,
        )
        proposals = _attach_structured_plan(
            proposals=proposals,
            parsed=fallback,
            week_start=week_start,
            macro_targets=macro_targets,
            personal_ctx=personal_ctx,
            state=state,
            user_msg=user_msg,
            proposal=proposal,
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
        personal_ctx.citations,
        citations_from_texts(rag_bits + [proposal] + memory_chunks + personal_ctx.chunks),
    )
    return {
        "proposals": proposals,
        "retrieved_context": (
            state.retrieved_context + memory_chunks + personal_ctx.chunks + rag_bits
        ),
        "citations": cites,
    }

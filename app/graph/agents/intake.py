"""Conversational onboarding / profile intake node."""
from __future__ import annotations

from app.config import get_llm
from app.graph.diet_gate import (
    diet_question_payload,
    looks_like_weight_decline,
    next_diet_slot,
    parse_activity_level,
    parse_height_cm_from_message,
    question_for_slot,
)
from app.graph.intake import (
    apply_extraction,
    extract_profile_facts,
    looks_like_confirmation_yes,
    next_intake_question,
    pending_intake_slot,
    profile_summary_line,
    required_slots_filled,
)
from app.graph.state import CoachingTeamState
from app.graph.weight_gate import (
    looks_like_first_plan_request,
    parse_weight_kg_from_message,
)
from app.memory.store import get_saved_week_plan, save_profile
from app.security import as_text, with_security, wrap_untrusted


def _handoff_first_plan(profile, state, *, preamble: str, provisional: bool = False) -> dict:
    profile.awaiting_weight_for_first_plan = False
    profile.awaiting_diet_slot = None
    save_profile(state.user_id, profile)
    proposals = {
        **{k: v for k, v in state.proposals.items()
           if k not in {"ask_weight_only", "ask_diet_slot"}},
        "intake_handoff": "first_plan",
        "plan_changed": False,
    }
    if provisional:
        proposals["macros_provisional_ok"] = True
    return {
        "profile": profile,
        "intent": "first_plan",
        "quick_replies": [],
        "messages": [{"role": "assistant", "content": preamble}],
        "proposals": proposals,
    }


def _ask_next_diet_slot(profile, state, *, after_slot: str | None = None) -> dict:
    nxt = next_diet_slot(profile)
    if nxt is None:
        from app.graph.tdee import compute_macro_targets

        targets = compute_macro_targets(
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            age=profile.age,
            sex=profile.sex,
            activity_level=profile.activity_level,  # type: ignore[arg-type]
            target_weight_kg=profile.target_weight_kg,
            goal=profile.goal,
        )
        if targets.is_estimate:
            preamble = (
                f"Got it — I'll draft your first week with "
                f"~{targets.calorie_target} kcal and ~{targets.protein_target_g}g protein "
                f"*(starting estimate — some details were skipped)*. "
                "You'll see workouts + meals on the approval card below."
            )
        else:
            preamble = (
                f"Got it — using Mifflin–St Jeor: ~{targets.calorie_target} kcal/day and "
                f"~{targets.protein_target_g}g protein. "
                "I'll draft your first week of workouts and meals — approval card below."
            )
        return _handoff_first_plan(
            profile, state, preamble=preamble, provisional=targets.is_estimate
        )
    payload = diet_question_payload(profile, nxt)
    save_profile(state.user_id, payload["profile"])
    return payload


def _handle_diet_gate(state: CoachingTeamState, profile, user_msg: str) -> dict:
    """One diet-metrics question per turn — hard stop, no plan."""
    slot = (
        state.proposals.get("ask_diet_slot")
        or profile.awaiting_diet_slot
        or ("weight" if profile.awaiting_weight_for_first_plan else None)
        or next_diet_slot(profile)
    )
    # Opening the gate this turn (user asked for a plan / confirmed onboarding).
    if state.proposals.get("ask_weight_only") or state.proposals.get("ask_diet_slot"):
        if looks_like_first_plan_request(user_msg) or looks_like_confirmation_yes(user_msg):
            slot = slot or next_diet_slot(profile) or "weight"
            payload = diet_question_payload(profile, slot)
            save_profile(state.user_id, payload["profile"])
            return payload

    if not slot:
        return _ask_next_diet_slot(profile, state)

    declined = looks_like_weight_decline(user_msg)

    if slot == "weight":
        parsed = parse_weight_kg_from_message(user_msg)
        if parsed is not None:
            profile.weight_kg = parsed
            profile.weight_declined = False
        elif declined:
            profile.weight_declined = True
            profile.weight_kg = None
        else:
            ext = extract_profile_facts(user_msg, pending_slot=None)
            profile = apply_extraction(profile, ext)
            if profile.weight_kg is None and not profile.weight_declined:
                q, chips = question_for_slot("weight")
                profile.awaiting_weight_for_first_plan = True
                save_profile(state.user_id, profile)
                return {
                    "profile": profile,
                    "intent": "intake",
                    "quick_replies": chips,
                    "messages": [{"role": "assistant", "content": q}],
                    "proposals": {"ask_diet_slot": "weight", "ask_weight_only": True, "plan_changed": False},
                }
        profile.awaiting_weight_for_first_plan = False
        return _ask_next_diet_slot(profile, state)

    if slot == "target_weight":
        parsed = parse_weight_kg_from_message(user_msg)
        if parsed is not None:
            profile.target_weight_kg = parsed
            profile.target_weight_declined = False
        elif declined:
            profile.target_weight_declined = True
            profile.target_weight_kg = None
        else:
            q, chips = question_for_slot("target_weight")
            profile.awaiting_diet_slot = "target_weight"
            save_profile(state.user_id, profile)
            return {
                "profile": profile,
                "intent": "intake",
                "quick_replies": chips,
                "messages": [{"role": "assistant", "content": q}],
                "proposals": {"ask_diet_slot": "target_weight", "plan_changed": False},
            }
        profile.awaiting_diet_slot = None
        return _ask_next_diet_slot(profile, state)

    if slot == "height":
        parsed = parse_height_cm_from_message(user_msg)
        if parsed is not None:
            profile.height_cm = parsed
            profile.height_declined = False
        elif declined:
            profile.height_declined = True
            profile.height_cm = None
        else:
            q, chips = question_for_slot("height")
            profile.awaiting_diet_slot = "height"
            save_profile(state.user_id, profile)
            return {
                "profile": profile,
                "intent": "intake",
                "quick_replies": chips,
                "messages": [{"role": "assistant", "content": q}],
                "proposals": {"ask_diet_slot": "height", "plan_changed": False},
            }
        profile.awaiting_diet_slot = None
        return _ask_next_diet_slot(profile, state)

    if slot == "activity":
        act = parse_activity_level(user_msg)
        if act:
            profile.activity_level = act
            profile.activity_declined = False
        elif declined:
            profile.activity_declined = True
            profile.activity_level = None
        else:
            q, chips = question_for_slot("activity")
            profile.awaiting_diet_slot = "activity"
            save_profile(state.user_id, profile)
            return {
                "profile": profile,
                "intent": "intake",
                "quick_replies": chips,
                "messages": [{"role": "assistant", "content": q}],
                "proposals": {"ask_diet_slot": "activity", "plan_changed": False},
            }
        profile.awaiting_diet_slot = None
        return _ask_next_diet_slot(profile, state)

    return _ask_next_diet_slot(profile, state)


def intake_node(state: CoachingTeamState) -> dict:
    """Extract → persist → ask one question (or confirm / hand off to first plan)."""
    last = state.messages[-1] if state.messages else None
    if last is None:
        user_msg = ""
    elif hasattr(last, "content"):
        user_msg = as_text(last.content)
    else:
        user_msg = as_text((last or {}).get("content", ""))  # type: ignore[union-attr]
    profile = state.profile.model_copy(deep=True)

    # --- Diet metrics gate (weight → target → height → activity) ---
    if (
        profile.awaiting_weight_for_first_plan
        or profile.awaiting_diet_slot
        or state.proposals.get("ask_weight_only")
        or state.proposals.get("ask_diet_slot")
    ):
        return _handle_diet_gate(state, profile, user_msg)

    # --- awaiting confirmation after required slots filled ---
    if profile.awaiting_onboarding_confirm and not profile.onboarding_complete:
        ext = extract_profile_facts(user_msg)
        if ext.confirmation == "yes" or looks_like_confirmation_yes(user_msg):
            profile.onboarding_complete = True
            profile.awaiting_onboarding_confirm = False
            from app.graph.diet_gate import needs_diet_gate_before_first_plan

            saved = get_saved_week_plan(state.user_id)
            if needs_diet_gate_before_first_plan(
                profile, week_plan=state.week_plan, saved_plan=saved
            ):
                slot = next_diet_slot(profile) or "weight"
                payload = diet_question_payload(profile, slot)
                save_profile(state.user_id, payload["profile"])
                return payload
            return _handoff_first_plan(
                profile,
                state,
                preamble=(
                    "Awesome — I'll draft your first week from that profile. "
                    "You'll see an approval card below before anything sticks."
                ),
            )
        profile = apply_extraction(profile, ext)
        if required_slots_filled(profile):
            profile.awaiting_onboarding_confirm = True
            save_profile(state.user_id, profile)
            return {
                "profile": profile,
                "intent": "intake",
                "quick_replies": ["Yes, looks good", "No, let me tweak"],
                "messages": [{"role": "assistant", "content": profile_summary_line(profile)}],
            }

    slot = pending_intake_slot(profile)
    ext = extract_profile_facts(user_msg, pending_slot=slot)
    profile = apply_extraction(profile, ext)

    aside = ""
    if ext.off_topic_question or (
        not any([
            ext.goal, ext.age is not None, ext.age_declined, ext.sex, ext.sex_declined,
            ext.weight_kg is not None, ext.weight_declined,
            ext.preferred_workout_modes, ext.food_preference,
            ext.sessions_per_week is not None, ext.constraints is not None,
            ext.constraints_none, ext.name,
        ])
        and len(user_msg.split()) > 4
        and "?" in user_msg
    ):
        q = ext.off_topic_question or user_msg
        try:
            aside_llm = get_llm(max_tokens=220)
            aside = as_text(aside_llm.invoke([
                {
                    "role": "system",
                    "content": with_security(
                        "You are SteadyFit coach mid-onboarding. Answer the user's "
                        "fitness question in 2-3 short warm sentences. Do not ask "
                        "onboarding questions — another turn will."
                    ),
                },
                {"role": "user", "content": wrap_untrusted(q, source="user")},
            ]).content).strip()
            if aside:
                aside = aside + "\n\n"
        except Exception:
            aside = ""

    save_profile(state.user_id, profile)

    if profile.onboarding_complete and not (
        profile.awaiting_weight_for_first_plan or profile.awaiting_diet_slot
    ):
        save_profile(state.user_id, profile)
        return {
            "profile": profile,
            "intent": "intake",
            "quick_replies": [],
            "messages": [{
                "role": "assistant",
                "content": (
                    f"Updated — thanks. {profile_summary_line(profile).replace('Got it — ', '').replace(' Does that look right?', '')} "
                    "I'll keep that in mind for the next re-plan."
                ),
            }],
        }

    if required_slots_filled(profile):
        profile.awaiting_onboarding_confirm = True
        save_profile(state.user_id, profile)
        return {
            "profile": profile,
            "intent": "intake",
            "quick_replies": ["Yes, looks good", "No, let me tweak"],
            "messages": [{
                "role": "assistant",
                "content": aside + profile_summary_line(profile),
            }],
        }

    prompt = next_intake_question(profile)
    if prompt is None:
        profile.awaiting_onboarding_confirm = True
        save_profile(state.user_id, profile)
        return {
            "profile": profile,
            "intent": "intake",
            "quick_replies": ["Yes, looks good"],
            "messages": [{"role": "assistant", "content": aside + profile_summary_line(profile)}],
        }

    return {
        "profile": profile,
        "intent": "intake",
        "quick_replies": prompt.quick_replies,
        "messages": [{"role": "assistant", "content": aside + prompt.question}],
    }

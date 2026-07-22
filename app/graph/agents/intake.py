"""Conversational onboarding / profile intake node."""
from __future__ import annotations

from app.config import get_llm
from app.graph.intake import (
    apply_extraction,
    extract_profile_facts,
    looks_like_confirmation_yes,
    next_intake_question,
    profile_summary_line,
    required_slots_filled,
)
from app.graph.state import CoachingTeamState
from app.memory.store import save_profile
from app.security import as_text, with_security, wrap_untrusted


def intake_node(state: CoachingTeamState) -> dict:
    """Extract → persist → ask one question (or confirm / hand off to first plan)."""
    user_msg = as_text(state.messages[-1].content) if state.messages else ""
    profile = state.profile.model_copy(deep=True)

    # --- awaiting confirmation after required slots filled ---
    if profile.awaiting_onboarding_confirm and not profile.onboarding_complete:
        ext = extract_profile_facts(user_msg)
        if ext.confirmation == "yes" or looks_like_confirmation_yes(user_msg):
            profile.onboarding_complete = True
            profile.awaiting_onboarding_confirm = False
            save_profile(state.user_id, profile)
            return {
                "profile": profile,
                "intent": "first_plan",
                "quick_replies": [],
                "messages": [{
                    "role": "assistant",
                    "content": (
                        "Awesome — I'll draft your first week from that profile. "
                        "You'll see an approval card below before anything sticks."
                    ),
                }],
                "proposals": {
                    **state.proposals,
                    "intake_handoff": "first_plan",
                },
            }
        # Treat as corrections and re-summarize
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

    ext = extract_profile_facts(user_msg)
    profile = apply_extraction(profile, ext)

    # Mid-onboarding off-topic: brief answer, then resume
    aside = ""
    if ext.off_topic_question or (
        not any([
            ext.goal, ext.age is not None, ext.age_declined, ext.sex, ext.sex_declined,
            ext.weight_kg is not None,
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

    # Profile update path after onboarding (re-entry)
    if profile.onboarding_complete:
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

"""Onboarding intake: completeness checks, extraction schema, question selection."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from app.config import get_llm, settings
from app.graph.state import (
    ACTIVITY_LEVEL_OPTIONS,
    FOOD_PREFERENCE_OPTIONS,
    WORKOUT_MODE_OPTIONS,
    UserProfile,
)
from app.security import as_text, wrap_untrusted

_DECLINE_RE = re.compile(
    r"(?i)^(prefer not to say|rather not say|skip(?: it)?|no thanks|pass)$"
)
_SESSIONS_BARE_RE = re.compile(r"^(?P<n>[1-7])(?:\s*x)?$")
_AGE_BARE_RE = re.compile(r"^(?P<n>\d{1,3})$")

REQUIRED_SLOTS = (
    "goal",
    "sessions_per_week",
    "preferred_workout_modes",
    "food_preference",
)
PRIORITY_SLOTS = (
    "goal",
    "sessions_per_week",
    "preferred_workout_modes",
    "food_preference",
    "age",
    "sex",
    "constraints",
)


class ProfileExtraction(BaseModel):
    """Only fields the user explicitly stated this turn. Unset = not mentioned."""
    goal: str | None = None
    age: int | None = None
    age_declined: bool = False
    sex: str | None = None
    sex_declined: bool = False
    weight_kg: float | None = None
    weight_declined: bool = False
    preferred_workout_modes: list[
        Literal["gym", "swimming", "walking", "running", "home", "cycling", "yoga"]
    ] | None = None
    food_preference: (
        Literal["vegetarian", "non-vegetarian", "vegan", "eggetarian", "no-preference"]
        | None
    ) = None
    sessions_per_week: int | None = None
    constraints: list[str] | None = None
    constraints_none: bool = False  # user said no injuries / no limits
    name: str | None = None
    confirmation: Literal["yes", "no", "unset"] = "unset"
    off_topic_question: str | None = None  # e.g. creatine ask mid-intake


class IntakePrompt(BaseModel):
    slot: str
    question: str
    quick_replies: list[str] = Field(default_factory=list)


EXTRACT_SYSTEM = """Extract profile facts the USER explicitly stated for a fitness onboarding form.
Return structured fields only. Rules:
- Never guess or invent facts that were not stated.
- Quick-reply chips send BARE short values with no sentence (e.g. "4", "gym", "vegetarian",
  "Prefer not to say"). Treat those as direct answers to the PENDING slot when one is named.
- If PENDING SLOT is sessions_per_week and the message is a lone integer 1-7, set sessions_per_week
  (NOT age). A bare "4" during the sessions question means 4 sessions/week.
- If PENDING SLOT is age and the message is a lone integer, set age (or age_declined for decline).
- preferred_workout_modes must be from: gym, swimming, walking, running, home, cycling, yoga.
- food_preference must be one of: vegetarian, non-vegetarian, vegan, eggetarian, no-preference.
- sessions_per_week: integer 1-7 if stated.
- age_declined / sex_declined: true if they prefer not to say / decline.
- sex: normalize to male, female, other, or prefer_not_to_say.
- weight_kg: body weight in kilograms if stated (convert lb/lbs to kg ≈ ×0.4536).
- weight_declined: true if they prefer not to say / skip / decline sharing weight.
- constraints: injuries or equipment limits they named; constraints_none if they said none.
- confirmation: yes/no only if they are confirming a profile summary; else unset.
- off_topic_question: if they asked a fitness FAQ instead of answering (e.g. creatine),
  copy that question briefly; else null.
- Leave fields null when not mentioned."""


def pending_intake_slot(profile: UserProfile) -> str | None:
    """First unfilled priority slot (the question we would ask next / just asked)."""
    prompt = next_intake_question(profile)
    return prompt.slot if prompt else None


def parse_chip_answer(message: str, pending_slot: str | None) -> ProfileExtraction | None:
    """Deterministic parse for quick-reply chip taps (bare values WE offered).

    Returns None when the message is not an unambiguous chip-style answer for
    the pending slot — caller should fall through to the LLM extractor.
    """
    if not pending_slot:
        return None
    raw = (message or "").strip()
    if not raw:
        return None
    lower = raw.lower()

    if pending_slot == "sessions_per_week":
        m = _SESSIONS_BARE_RE.match(lower)
        if m:
            return ProfileExtraction(sessions_per_week=int(m.group("n")))
        return None

    if pending_slot == "age":
        if _DECLINE_RE.match(raw):
            return ProfileExtraction(age_declined=True)
        m = _AGE_BARE_RE.match(raw)
        if m:
            return ProfileExtraction(age=int(m.group("n")))
        return None

    if pending_slot == "sex":
        if _DECLINE_RE.match(raw):
            return ProfileExtraction(sex_declined=True)
        sex_map = {
            "male": "male",
            "m": "male",
            "female": "female",
            "f": "female",
            "other": "other",
            "prefer_not_to_say": "prefer_not_to_say",
            "prefer not to say": "prefer_not_to_say",
        }
        if lower in sex_map:
            return ProfileExtraction(sex=sex_map[lower])
        return None

    if pending_slot == "food_preference":
        for opt in FOOD_PREFERENCE_OPTIONS:
            if lower == opt.lower():
                return ProfileExtraction(food_preference=opt)  # type: ignore[arg-type]
        return None

    if pending_slot == "preferred_workout_modes":
        # Single chip tap, or a short comma/and list of chip labels.
        aliases = {
            "home workouts": "home",
            "home workout": "home",
        }
        parts = [
            p.strip().lower()
            for p in re.split(r"\s*(?:,|/|&| and )\s*", lower)
            if p.strip()
        ]
        if not parts:
            parts = [lower]
        modes: list[str] = []
        for part in parts:
            part = aliases.get(part, part)
            if part in WORKOUT_MODE_OPTIONS and part not in modes:
                modes.append(part)
        if modes and len(modes) == len(parts):
            return ProfileExtraction(preferred_workout_modes=modes)  # type: ignore[arg-type]
        return None

    if pending_slot == "constraints":
        if lower in {"none", "no", "n/a", "na", "nothing", "all clear"}:
            return ProfileExtraction(constraints_none=True)
        return None

    if pending_slot == "activity":
        if _DECLINE_RE.match(raw):
            return ProfileExtraction()  # decline handled by diet_gate
        act = lower.replace(" ", "_").replace("-", "_")
        aliases = {
            "sedentary": "sedentary",
            "light": "light",
            "lightly_active": "light",
            "moderate": "moderate",
            "moderately_active": "moderate",
            "active": "active",
            "very_active": "active",
        }
        mapped = aliases.get(act)
        if mapped and mapped in ACTIVITY_LEVEL_OPTIONS:
            # Stored via diet_gate apply path; extraction stays empty for LLM fallback.
            return ProfileExtraction()
        return None

    return None


def slot_filled(profile: UserProfile, slot: str) -> bool:
    if slot == "goal":
        return bool(profile.goal and profile.goal.strip())
    if slot == "sessions_per_week":
        return profile.sessions_per_week is not None
    if slot == "preferred_workout_modes":
        return bool(profile.preferred_workout_modes)
    if slot == "food_preference":
        return profile.food_preference is not None
    if slot == "age":
        return profile.age is not None or profile.age_declined
    if slot == "sex":
        return bool(profile.sex) or profile.sex_declined
    if slot == "constraints":
        return profile.constraints_asked or bool(profile.constraints)
    return False


def required_slots_filled(profile: UserProfile) -> bool:
    return all(slot_filled(profile, s) for s in REQUIRED_SLOTS)


def needs_intake(profile: UserProfile) -> bool:
    if profile.awaiting_weight_for_first_plan or profile.awaiting_diet_slot:
        return True
    if profile.onboarding_complete:
        return False
    return not required_slots_filled(profile) or profile.awaiting_onboarding_confirm


def apply_extraction(profile: UserProfile, ext: ProfileExtraction) -> UserProfile:
    data = profile.model_dump()
    if ext.name:
        data["name"] = ext.name.strip()
    if ext.goal:
        data["goal"] = ext.goal.strip()
    if ext.age is not None:
        data["age"] = max(13, min(100, ext.age))
        data["age_declined"] = False
    if ext.age_declined:
        data["age_declined"] = True
        data["age"] = None
    if ext.sex:
        sex = ext.sex.strip().lower().replace(" ", "_")
        if sex in {"m", "male", "man"}:
            sex = "male"
        elif sex in {"f", "female", "woman"}:
            sex = "female"
        data["sex"] = sex
        data["sex_declined"] = sex == "prefer_not_to_say"
    if ext.sex_declined:
        data["sex_declined"] = True
        data["sex"] = "prefer_not_to_say"
    if ext.weight_kg is not None:
        data["weight_kg"] = max(30.0, min(300.0, float(ext.weight_kg)))
        data["weight_declined"] = False
    if ext.weight_declined:
        data["weight_declined"] = True
    if ext.preferred_workout_modes:
        modes = [m for m in ext.preferred_workout_modes if m in WORKOUT_MODE_OPTIONS]
        if modes:
            # merge unique, preserve order
            existing = list(data.get("preferred_workout_modes") or [])
            for m in modes:
                if m not in existing:
                    existing.append(m)
            data["preferred_workout_modes"] = existing
    if ext.food_preference:
        data["food_preference"] = ext.food_preference
    if ext.sessions_per_week is not None:
        data["sessions_per_week"] = max(1, min(7, ext.sessions_per_week))
    if ext.constraints is not None:
        data["constraints"] = [c.strip() for c in ext.constraints if c.strip()]
        data["constraints_asked"] = True
    if ext.constraints_none:
        data["constraints"] = []
        data["constraints_asked"] = True
    return UserProfile(**data)


def extract_profile_facts(
    message: str,
    *,
    pending_slot: str | None = None,
) -> ProfileExtraction:
    """Extract facts; chip taps for the pending slot are deterministic (no LLM)."""
    chip = parse_chip_answer(message, pending_slot)
    if chip is not None:
        return chip

    llm = get_llm(settings.judge_model, temperature=0, max_tokens=400)
    structured = llm.with_structured_output(ProfileExtraction)
    slot_hint = (
        f"\nPENDING SLOT for this turn: {pending_slot}\n"
        "If the user sent a bare chip value, fill that slot."
        if pending_slot
        else "\nPENDING SLOT: unknown — do not map a lone digit to age unless they said age.\n"
    )
    try:
        result = structured.invoke([
            {"role": "system", "content": EXTRACT_SYSTEM + slot_hint},
            {"role": "user", "content": wrap_untrusted(message, source="user")},
        ])
        if isinstance(result, ProfileExtraction):
            return result
        return ProfileExtraction.model_validate(result)
    except Exception:
        return ProfileExtraction()


def build_question(slot: str, profile: UserProfile) -> IntakePrompt:
    goal = profile.goal or "your fitness goal"
    if slot == "goal":
        return IntakePrompt(
            slot=slot,
            question=(
                "Hey — I'm Steady, your coach. What's your main fitness goal right now? "
                "(e.g. lose fat, build strength, stay consistent while busy.)"
            ),
        )
    if slot == "sessions_per_week":
        return IntakePrompt(
            slot=slot,
            question=(
                f"Got it — aiming for {goal}. How many training sessions per week "
                "feel realistic for your schedule?"
            ),
            quick_replies=["2", "3", "4", "5"],
        )
    if slot == "preferred_workout_modes":
        return IntakePrompt(
            slot=slot,
            question=(
                "Which ways do you like to move? Tap any that fit — gym, walking, "
                "running, home workouts, swimming, cycling, or yoga."
            ),
            quick_replies=list(WORKOUT_MODE_OPTIONS),
        )
    if slot == "food_preference":
        return IntakePrompt(
            slot=slot,
            question="How do you usually eat? Pick the closest option.",
            quick_replies=list(FOOD_PREFERENCE_OPTIONS),
        )
    if slot == "age":
        return IntakePrompt(
            slot=slot,
            question=(
                "Optional — what's your age? It helps me keep intensity sensible. "
                "You can also prefer not to say."
            ),
            quick_replies=["Prefer not to say"],
        )
    if slot == "sex":
        return IntakePrompt(
            slot=slot,
            question=(
                "Optional — sex used for baseline calorie estimates. "
                "Prefer not to say is totally fine."
            ),
            quick_replies=["male", "female", "other", "Prefer not to say"],
        )
    if slot == "constraints":
        return IntakePrompt(
            slot=slot,
            question=(
                "Any injuries or equipment limits I should work around? "
                "Say \"none\" if you're all clear."
            ),
            quick_replies=["None"],
        )
    return IntakePrompt(slot=slot, question="Tell me a bit more so I can help.")


def next_intake_question(profile: UserProfile) -> IntakePrompt | None:
    for slot in PRIORITY_SLOTS:
        if not slot_filled(profile, slot):
            return build_question(slot, profile)
    return None


def profile_summary_line(profile: UserProfile) -> str:
    modes = ", ".join(profile.preferred_workout_modes) or "flexible training"
    food = profile.food_preference or "no strong food preference"
    sessions = profile.sessions_per_week or 3
    bits = [
        f"goal: {profile.goal}",
        f"{sessions}x/week",
        f"modes: {modes}",
        f"food: {food}",
    ]
    if profile.age is not None:
        bits.append(f"age {profile.age}")
    if profile.sex and profile.sex != "prefer_not_to_say":
        bits.append(profile.sex)
    if profile.constraints:
        bits.append(f"constraints: {', '.join(profile.constraints)}")
    return "Got it — " + "; ".join(bits) + ". Does that look right?"


def looks_like_confirmation_yes(text: str) -> bool:
    t = text.strip().lower()
    return t in {
        "yes", "y", "yeah", "yep", "yup", "correct", "looks good", "sounds good",
        "confirm", "ok", "okay", "sure", "that's right", "thats right", "perfect",
    }


def looks_like_profile_change_request(text: str) -> bool:
    t = text.lower()
    triggers = (
        "change my goal", "update my goal", "new goal", "i've gone vegan",
        "i have gone vegan", "now vegan", "change my food", "switch to",
        "prefer vegetarian", "sessions per week", "workout mode",
    )
    return any(x in t for x in triggers)

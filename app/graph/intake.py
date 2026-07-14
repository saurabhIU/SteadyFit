"""Onboarding intake: completeness checks, extraction schema, question selection."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.config import get_llm, settings
from app.graph.state import (
    FOOD_PREFERENCE_OPTIONS,
    WORKOUT_MODE_OPTIONS,
    UserProfile,
)
from app.security import as_text, wrap_untrusted

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
- preferred_workout_modes must be from: gym, swimming, walking, running, home, cycling, yoga.
- food_preference must be one of: vegetarian, non-vegetarian, vegan, eggetarian, no-preference.
- sessions_per_week: integer 1-7 if stated.
- age_declined / sex_declined: true if they prefer not to say / decline.
- sex: normalize to male, female, other, or prefer_not_to_say.
- constraints: injuries or equipment limits they named; constraints_none if they said none.
- confirmation: yes/no only if they are confirming a profile summary; else unset.
- off_topic_question: if they asked a fitness FAQ instead of answering (e.g. creatine),
  copy that question briefly; else null.
- Leave fields null when not mentioned."""


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


def extract_profile_facts(message: str) -> ProfileExtraction:
    llm = get_llm(settings.judge_model, temperature=0, max_tokens=400)
    structured = llm.with_structured_output(ProfileExtraction)
    try:
        result = structured.invoke([
            {"role": "system", "content": EXTRACT_SYSTEM},
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

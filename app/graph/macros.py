"""Shared helpers for provisional macro framing (incomplete TDEE inputs)."""
from __future__ import annotations

from app.graph.state import UserProfile


def has_body_stats(profile: UserProfile | None) -> bool:
    """True when weight is on file (legacy check used by older prompts)."""
    if profile is None:
        return False
    return profile.weight_kg is not None and float(profile.weight_kg) > 0


def macros_provisional(profile: UserProfile | None) -> bool:
    """True when code-computed TDEE used defaults (missing weight/height/etc.)."""
    if profile is None:
        return True
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
    return targets.is_estimate


PROVISIONAL_MACRO_INSTRUCTIONS = """
PROVISIONAL MACRO TARGETS (CRITICAL when TDEE inputs are incomplete):
- You may still suggest starting calorie/protein numbers.
- EVERY time you state a calorie or protein target, put the caveat INLINE
  next to the number, e.g.:
  "~1,800 kcal *(starting estimate — refine later with weight/height)*"
  "~120g protein *(starting estimate — refine later with weight/height)*"
- Do NOT re-ask for weight/height/activity if those were already declined.
- Never present targets as precisely computed when weight or height is missing.
- This rule still applies AFTER a plan is approved/saved — saved numbers stay
  provisional estimates until weight_kg + height_cm are on the profile.
""".strip()

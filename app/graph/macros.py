"""Shared helpers for provisional macro framing (no weight/body stats yet)."""
from __future__ import annotations

from app.graph.state import UserProfile


def has_body_stats(profile: UserProfile | None) -> bool:
    """True when we have enough body data to treat targets as personalized."""
    if profile is None:
        return False
    return profile.weight_kg is not None and float(profile.weight_kg) > 0


def macros_provisional(profile: UserProfile | None) -> bool:
    return not has_body_stats(profile)


PROVISIONAL_MACRO_INSTRUCTIONS = """
PROVISIONAL MACRO TARGETS (CRITICAL when the profile has no weight_kg):
- You may still suggest starting calorie/protein numbers.
- EVERY time you state a calorie or protein target, put the caveat INLINE
  next to the number, e.g.:
  "~1,800 kcal *(starting estimate — share your weight to refine this)*"
  "~120g protein *(starting estimate — share your weight to refine this)*"
- In the SAME reply, ask a direct follow-up for the missing data, e.g.
  "What's your current weight? I'll tighten these targets once I know."
- Never present targets as precisely computed for this person without weight.
- This rule still applies AFTER a plan is approved/saved — saved numbers stay
  provisional estimates until weight_kg is on the profile.
""".strip()

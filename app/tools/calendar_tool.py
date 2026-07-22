"""Calendar tool. Real Google Calendar OAuth is a stretch goal.

Until a real per-user calendar is connected, this returns NO conflicts.
Never inject demo/mock busy blocks — that caused fabricated "your travel"
claims for brand-new try-* profiles.
"""
from __future__ import annotations


def get_calendar_conflicts(user_id: str | None = None) -> list[dict]:
    """Return busy blocks for this user.

    Empty until a real calendar source is wired. ``user_id`` is accepted for
    forward compatibility; mock JSON is intentionally not used.
    """
    return []

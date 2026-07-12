"""Calendar tool. Mock JSON for MVP; swap in Google Calendar API as stretch goal."""
import json
from pathlib import Path

MOCK = Path("data/mock_calendar.json")


def get_calendar_conflicts() -> list[dict]:
    if MOCK.exists():
        return json.loads(MOCK.read_text())
    return [
        {"day": "Tue", "busy": "09:00-19:00", "reason": "back-to-back meetings"},
        {"day": "Wed", "busy": "all-day", "reason": "flight to client site"},
    ]

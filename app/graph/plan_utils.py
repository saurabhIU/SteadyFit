"""Helpers to extract structured week plans from specialist LLM output."""
import json
import re
from datetime import date

from app.graph.state import WeekPlan, WorkoutDay


def _extract_json_blob(text: str) -> dict | None:
    """Pull the first JSON object from markdown fences or raw text."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def parse_week_plan(text: str) -> WeekPlan | None:
    """Best-effort parse of scheduler JSON into a WeekPlan."""
    data = _extract_json_blob(text)
    if not data:
        return None
    try:
        days = [
            WorkoutDay(**d) if isinstance(d, dict) else d
            for d in data.get("days", [])
        ]
        return WeekPlan(
            week_start=data.get("week_start") or date.today().isoformat(),
            days=days,
            calorie_target=int(data.get("calorie_target", 2200)),
            protein_target_g=int(data.get("protein_target_g", 150)),
            notes=str(data.get("notes", "")),
        )
    except (TypeError, ValueError):
        return None

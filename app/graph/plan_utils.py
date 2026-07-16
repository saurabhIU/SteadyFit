"""Helpers to extract structured week plans from specialist LLM output."""
import json
import re
from datetime import date

from app.graph.state import WeekPlan, WorkoutDay

_VALID_STATUS = frozenset({"planned", "done", "skipped", "moved"})


def _loads_object(text: str) -> dict | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _balanced_object_from(text: str, start: int) -> str | None:
    """Return the JSON object substring starting at ``text[start] == '{'``."""
    if start < 0 or start >= len(text) or text[start] != "{":
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _looks_like_week_plan(data: dict) -> bool:
    return "days" in data or "week_start" in data


def _extract_json_blob(text: str) -> dict | None:
    """Pull a WeekPlan-shaped JSON object from markdown fences or raw text."""
    # Prefer fenced blocks; use balanced braces (non-greedy .*? breaks on nested days).
    for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", text):
        blob = m.group(1).strip()
        if blob.startswith("{"):
            candidate = _balanced_object_from(blob, 0) or blob
            data = _loads_object(candidate)
            if data and _looks_like_week_plan(data):
                return data

    # Scan every object; prefer ones that look like a week plan.
    for match in re.finditer(r"\{", text):
        candidate = _balanced_object_from(text, match.start())
        if not candidate:
            continue
        data = _loads_object(candidate)
        if data and _looks_like_week_plan(data):
            return data
    return None


def _parse_day(raw: object) -> WorkoutDay | None:
    if not isinstance(raw, dict):
        return None
    day = str(raw.get("day") or "").strip()
    focus = str(raw.get("focus") or "").strip()
    if not day or not focus:
        return None
    try:
        duration = int(raw.get("duration_min", 45))
    except (TypeError, ValueError):
        duration = 45
    status = raw.get("status", "planned")
    if status not in _VALID_STATUS:
        status = "planned"
    return WorkoutDay(day=day, focus=focus, duration_min=duration, status=status)


def parse_week_plan(text: str) -> WeekPlan | None:
    """Best-effort parse of scheduler JSON into a WeekPlan."""
    data = _extract_json_blob(text)
    if not data:
        return None
    try:
        days = [d for d in (_parse_day(x) for x in data.get("days", [])) if d is not None]
        week_start = str(data.get("week_start") or date.today().isoformat())[:10]
        return WeekPlan(
            week_start=week_start,
            days=days,
            calorie_target=int(data.get("calorie_target", 2200)),
            protein_target_g=int(data.get("protein_target_g", 150)),
            notes=str(data.get("notes", "")),
        )
    except (TypeError, ValueError):
        return None


def coerce_week_plan(raw: object) -> WeekPlan | None:
    """Normalize checkpoint / proposal payloads into a WeekPlan."""
    if raw is None:
        return None
    if isinstance(raw, WeekPlan):
        return raw
    if isinstance(raw, dict):
        try:
            days = [d for d in (_parse_day(x) for x in raw.get("days", [])) if d is not None]
            week_start = str(raw.get("week_start") or "").strip()
            if not week_start:
                return None
            return WeekPlan(
                week_start=week_start[:10],
                days=days,
                calorie_target=int(raw.get("calorie_target", 2200)),
                protein_target_g=int(raw.get("protein_target_g", 150)),
                notes=str(raw.get("notes", "")),
            )
        except (TypeError, ValueError):
            return None
    return None

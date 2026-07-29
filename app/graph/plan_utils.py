"""Helpers to extract structured week plans from specialist LLM output."""
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.graph.state import WeekPlan, WorkoutDay

_VALID_STATUS = frozenset({"planned", "done", "skipped", "moved"})

# Mirrors web/lib/plan-dates.ts — week_start is Monday; offsets Mon=+0 … Sun=+6.
_WEEKDAY_OFFSET: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

_WEEKDAY_FULL: tuple[str, ...] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
_WEEKDAY_ABBR: tuple[str, ...] = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# Relative day words → offset from as_of (0=today).
_RELATIVE_OFFSETS: dict[str, int] = {
    "today": 0,
    "tonight": 0,
    "tomorrow": 1,
    "yesterday": -1,
}

_RELATIVE_TOKEN_RE = re.compile(
    r"(?is)\b(today|tonight|tomorrow|yesterday)\b"
)
_NAMED_WEEKDAY_RE = re.compile(
    r"(?is)\b(monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|fri|"
    r"saturday|sat|sunday|sun)\b"
)
# Informational "what's my plan for tomorrow / today" — no adjust verbs.
_INFO_PLAN_DAY_RE = re.compile(
    r"(?is)\b(?:"
    r"what(?:'?s|\s+is|\s+are)?\s+(?:my\s+)?(?:plan|workout|session|schedule)"
    r"\s+for\s+(?:this\s+)?"
    r"|"
    r"what\s+(?:do\s+i\s+have|am\s+i\s+(?:doing|training|scheduled))"
    r"\s+(?:on\s+|for\s+)?"
    r"|"
    r"(?:show|tell)\s+me\s+(?:my\s+)?(?:plan|workout)\s+for\s+"
    r")"
    r"(today|tonight|tomorrow|yesterday|"
    r"monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|fri|"
    r"saturday|sat|sunday|sun)\b"
)
_PLAN_ADJUST_RE = re.compile(
    r"(?is)\b("
    r"readjust|re-?adjust|adjust|shorten|only\s+have|move|reschedule|change|"
    r"trim|swap|rebuild|rewrite|make\s+it|cut\s+(?:it\s+)?(?:to|down)|"
    r"\d+\s*min(?:ute)?s?"
    r")\b"
)


def weekday_offset(day_name: str) -> int | None:
    key = (day_name or "").strip().lower()
    return _WEEKDAY_OFFSET.get(key)


def weekday_full_name(d: date) -> str:
    return _WEEKDAY_FULL[d.weekday()]


def weekday_abbr(d: date) -> str:
    return _WEEKDAY_ABBR[d.weekday()]


def date_for_weekday(week_start: str | date, day_name: str) -> date | None:
    """Calendar date for a named weekday in the week starting at week_start (Mon)."""
    if isinstance(week_start, date):
        start = week_start
    else:
        try:
            start = date.fromisoformat(str(week_start)[:10])
        except ValueError:
            return None
    off = weekday_offset(day_name)
    if off is None:
        return None
    return start + timedelta(days=off)


def current_week_monday(as_of: date | None = None) -> date:
    """ISO week start (Monday) for the calendar week containing ``as_of``."""
    d = as_of or date.today()
    return d - timedelta(days=d.weekday())


def current_week_start_iso(as_of: date | None = None) -> str:
    return current_week_monday(as_of).isoformat()


@dataclass(frozen=True)
class ResolvedRelativeDay:
    """Deterministic resolution of today/tomorrow/named weekday — never LLM."""

    token: str  # raw relative/named token from the user text
    target: date
    weekday_full: str
    weekday_abbr: str
    offset_days: int  # vs as_of (0=today)


def resolve_relative_day(
    text: str,
    *,
    as_of: date | None = None,
) -> ResolvedRelativeDay | None:
    """Resolve the first relative/named day reference in ``text`` via calendar math.

    Same source of truth as week_start / day-tile rendering (`date.today()` +
    Monday-based offsets). Prefer relative tokens (today/tomorrow) over named
    weekdays when both appear.
    """
    today = as_of or date.today()
    raw = (text or "").strip()
    if not raw:
        return None

    rel = _RELATIVE_TOKEN_RE.search(raw)
    if rel:
        token = rel.group(1).lower()
        off = _RELATIVE_OFFSETS[token]
        target = today + timedelta(days=off)
        return ResolvedRelativeDay(
            token=token,
            target=target,
            weekday_full=weekday_full_name(target),
            weekday_abbr=weekday_abbr(target),
            offset_days=off,
        )

    named = _NAMED_WEEKDAY_RE.search(raw)
    if named:
        token = named.group(1)
        off = weekday_offset(token)
        if off is None:
            return None
        monday = current_week_monday(today)
        target = monday + timedelta(days=off)
        return ResolvedRelativeDay(
            token=token.lower(),
            target=target,
            weekday_full=weekday_full_name(target),
            weekday_abbr=weekday_abbr(target),
            offset_days=(target - today).days,
        )
    return None


def workout_day_on_date(
    week_plan: WeekPlan | None,
    target: date,
) -> WorkoutDay | None:
    """Return the WorkoutDay whose weekday maps to ``target`` under week_start."""
    if not week_plan or not week_plan.days:
        return None
    for day in week_plan.days:
        day_date = date_for_weekday(week_plan.week_start, day.day)
        if day_date == target:
            return day
    return None


def looks_like_informational_day_plan_query(text: str) -> bool:
    """True for 'what's my plan for tomorrow' — False when also asking to adjust."""
    raw = (text or "").strip()
    if not raw:
        return False
    if not _INFO_PLAN_DAY_RE.search(raw):
        return False
    # Adjust verbs / durations → plan-changing path (still uses calendar_truth_block).
    if _PLAN_ADJUST_RE.search(raw):
        return False
    return True


def calendar_truth_block(
    week_plan: WeekPlan | None,
    user_msg: str = "",
    *,
    as_of: date | None = None,
) -> str:
    """Hard calendar facts for any scheduler / coach reply path.

    Models must treat this as ground truth — never invent a different weekday
    for today/tomorrow.
    """
    today = as_of or date.today()
    tomorrow = today + timedelta(days=1)
    monday = current_week_monday(today)
    lines = [
        "CALENDAR TRUTH (computed in code — NEVER invent a different weekday):",
        f"- Today is {weekday_full_name(today)} {today.isoformat()} "
        f"(abbr {weekday_abbr(today)}).",
        f"- Tomorrow is {weekday_full_name(tomorrow)} {tomorrow.isoformat()} "
        f"(abbr {weekday_abbr(tomorrow)}).",
        f"- This week's Monday (week_start) is {monday.isoformat()}.",
    ]
    if week_plan and week_plan.days:
        lines.append(
            f"- Active plan week_start={week_plan.week_start}."
        )
        for day in week_plan.days:
            day_date = date_for_weekday(week_plan.week_start, day.day)
            if day_date is None:
                continue
            label = ""
            if day_date == today:
                label = " ← TODAY"
            elif day_date == tomorrow:
                label = " ← TOMORROW"
            lines.append(
                f"  - {weekday_full_name(day_date)} ({day.day}) "
                f"{day_date.isoformat()}: {day.focus} "
                f"({day.duration_min} min, {day.status}){label}"
            )
        today_day = workout_day_on_date(week_plan, today)
        tomorrow_day = workout_day_on_date(week_plan, tomorrow)
        if today_day is None:
            lines.append("- Today has no planned session on this week_plan (rest / empty).")
        if tomorrow_day is None:
            lines.append(
                "- Tomorrow has no planned session on this week_plan (rest / empty)."
            )

    resolved = resolve_relative_day(user_msg, as_of=today) if user_msg else None
    if resolved:
        session = workout_day_on_date(week_plan, resolved.target)
        if session:
            lines.append(
                f"- User referred to '{resolved.token}' → "
                f"{resolved.weekday_full} {resolved.target.isoformat()} → "
                f"{session.focus} ({session.duration_min} min)."
            )
        else:
            lines.append(
                f"- User referred to '{resolved.token}' → "
                f"{resolved.weekday_full} {resolved.target.isoformat()} "
                f"(no planned session that day)."
            )
        lines.append(
            f"When answering, you MUST name {resolved.weekday_full} for "
            f"'{resolved.token}' — never a different weekday."
        )
    return "\n".join(lines)


def build_informational_day_plan_reply(
    *,
    profile_name: str,
    week_plan: WeekPlan | None,
    user_msg: str,
    as_of: date | None = None,
) -> str | None:
    """Deterministic reply for informational day-plan questions (no HITL)."""
    if not looks_like_informational_day_plan_query(user_msg):
        return None
    resolved = resolve_relative_day(user_msg, as_of=as_of)
    if resolved is None:
        return None
    name = (profile_name or "").strip() or "there"
    session = workout_day_on_date(week_plan, resolved.target)
    token_label = resolved.token
    if token_label in {"today", "tonight", "tomorrow", "yesterday"}:
        lead = (
            f"{token_label.capitalize()} is **{resolved.weekday_full}** "
            f"({resolved.target.isoformat()})"
        )
    else:
        lead = (
            f"**{resolved.weekday_full}** ({resolved.target.isoformat()})"
        )

    if session is None:
        return (
            f"Hey {name}! {lead}. There's no planned workout on that day "
            f"in your current week — it's a rest / unscheduled day. "
            f"Want me to add something light?"
        )
    return (
        f"Hey {name}! {lead}, and you've got **{session.focus}** scheduled — "
        f"**{session.duration_min} minutes** ({session.status})."
    )


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

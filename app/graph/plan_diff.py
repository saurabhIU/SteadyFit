"""Deterministic week-plan diffs for plan_changed chat replies.

Single source of truth for "what actually changed" — used by coaching_team
composition so specialist specifics (day, duration, memory cites) reach the
user-facing reply instead of a vague template intro.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from app.graph.plan_utils import (
    coerce_week_plan,
    date_for_weekday,
    resolve_relative_day,
    weekday_full_name,
)
from app.graph.state import WeekPlan, WorkoutDay

ChangeKind = Literal["duration", "focus", "status", "added", "removed", "mixed"]

_DURATION_RE = re.compile(
    r"(?is)\b(\d{1,3})\s*(?:-|–|to)?\s*(?:min(?:ute)?s?)\b"
)
# Require whitespace before the separator so we don't chop inside "(30-min)".
_FOCUS_CORE_RE = re.compile(r"\s+[—–\-:].*$")


@dataclass(frozen=True)
class DayChange:
    """One day that differs between prior and proposed plans."""

    day_abbr: str
    weekday_full: str
    kind: ChangeKind
    old: WorkoutDay | None
    new: WorkoutDay | None
    requested: bool = False  # matches what the user asked this turn

    @property
    def old_duration(self) -> int | None:
        return None if self.old is None else int(self.old.duration_min)

    @property
    def new_duration(self) -> int | None:
        return None if self.new is None else int(self.new.duration_min)

    @property
    def old_focus(self) -> str:
        return (self.old.focus if self.old else "") or ""

    @property
    def new_focus(self) -> str:
        return (self.new.focus if self.new else "") or ""


@dataclass
class PlanDiff:
    """Structured prior → proposed delta + memory tags used this turn."""

    is_first_plan: bool
    changes: list[DayChange] = field(default_factory=list)
    memory_tags: list[str] = field(default_factory=list)

    @property
    def requested(self) -> list[DayChange]:
        return [c for c in self.changes if c.requested]

    @property
    def secondary(self) -> list[DayChange]:
        return [c for c in self.changes if not c.requested]


def _norm_day_key(day_name: str) -> str:
    raw = (day_name or "").strip().lower()
    aliases = {
        "monday": "mon",
        "mon": "mon",
        "tuesday": "tue",
        "tue": "tue",
        "wednesday": "wed",
        "wed": "wed",
        "thursday": "thu",
        "thu": "thu",
        "friday": "fri",
        "fri": "fri",
        "saturday": "sat",
        "sat": "sat",
        "sunday": "sun",
        "sun": "sun",
    }
    return aliases.get(raw, raw[:3] if raw else "")


def _focus_core(focus: str) -> str:
    """Compare session identity, ignoring trailing exercise-detail rewrites."""
    text = (focus or "").strip()
    text = _FOCUS_CORE_RE.sub("", text).strip()
    text = re.sub(r"\[.*?\]", "", text).strip()
    return re.sub(r"\s+", " ", text).lower()


_REST_FOCUS_RE = re.compile(r"(?is)\b(rest|recovery|off\s*day|active\s*recovery)\b")


def _is_rest_day(day: WorkoutDay | None) -> bool:
    """True for rest/recovery days (focus keyword and/or zero-duration rest)."""
    if day is None:
        return False
    focus = (day.focus or "").strip()
    if _REST_FOCUS_RE.search(focus):
        return True
    # Zero-duration with empty/placeholder focus also counts as rest.
    return int(day.duration_min or 0) == 0 and (
        not focus or focus.lower() in {"—", "-", "n/a", "none"}
    )


def _is_noise_rest_change(old: WorkoutDay | None, new: WorkoutDay | None) -> bool:
    """Rest kept as rest, or a rest day removed — not worth reporting."""
    if new is None and _is_rest_day(old):
        return True
    if _is_rest_day(old) and _is_rest_day(new):
        return True
    return False


def _day_map(plan: WeekPlan | None) -> dict[str, WorkoutDay]:
    if not plan or not plan.days:
        return {}
    out: dict[str, WorkoutDay] = {}
    for d in plan.days:
        key = _norm_day_key(d.day)
        if key:
            out[key] = d
    return out


def _weekday_label(
    plan: WeekPlan | None, day_abbr: str, fallback_day: WorkoutDay | None
) -> str:
    name = (fallback_day.day if fallback_day else day_abbr) or day_abbr
    if plan and plan.week_start:
        d = date_for_weekday(plan.week_start, name)
        if d is not None:
            return weekday_full_name(d)
    full = {
        "mon": "Monday",
        "tue": "Tuesday",
        "wed": "Wednesday",
        "thu": "Thursday",
        "fri": "Friday",
        "sat": "Saturday",
        "sun": "Sunday",
    }
    return full.get(_norm_day_key(day_abbr), name.title())


def _classify(old: WorkoutDay | None, new: WorkoutDay | None) -> ChangeKind | None:
    if old is None and new is None:
        return None
    if old is None:
        return "added"
    if new is None:
        return "removed"
    dur_changed = int(old.duration_min) != int(new.duration_min)
    focus_changed = _focus_core(old.focus) != _focus_core(new.focus)
    detail_only = (
        not dur_changed
        and not focus_changed
        and (old.focus or "").strip() != (new.focus or "").strip()
    )
    status_changed = (old.status or "") != (new.status or "")
    if detail_only and not status_changed:
        return "focus"
    if dur_changed and (focus_changed or detail_only):
        return "mixed"
    if dur_changed:
        return "duration"
    if focus_changed or detail_only:
        return "focus"
    if status_changed:
        return "status"
    return None


def _requested_day_keys(user_msg: str, *, as_of: date | None = None) -> set[str]:
    """Which weekdays the user explicitly targeted this turn."""
    keys: set[str] = set()
    resolved = resolve_relative_day(user_msg or "", as_of=as_of)
    if resolved is not None:
        keys.add(_norm_day_key(resolved.weekday_abbr))
    for m in re.finditer(
        r"(?is)\b(monday|mon|tuesday|tue|wednesday|wed|thursday|thu|"
        r"friday|fri|saturday|sat|sunday|sun)\b",
        user_msg or "",
    ):
        keys.add(_norm_day_key(m.group(1)))
    return keys


def _requested_duration(user_msg: str) -> int | None:
    m = _DURATION_RE.search(user_msg or "")
    if not m:
        return None
    try:
        val = int(m.group(1))
    except ValueError:
        return None
    return val if 5 <= val <= 180 else None


def memory_tags_from_citations(citations: list | None) -> list[str]:
    """Deduped [Memory: week of YYYY-MM-DD] tags present this turn."""
    tags: list[str] = []
    seen: set[str] = set()
    for c in citations or []:
        if not isinstance(c, dict):
            continue
        kind = str(c.get("kind") or "").lower()
        tag = str(c.get("tag") or "").strip()
        if not tag and kind == "memory":
            week = str(c.get("section") or c.get("source_file") or "")
            m = re.search(r"(\d{4}-\d{2}-\d{2})", week)
            if m:
                tag = f"[Memory: week of {m.group(1)}]"
        if not tag.startswith("[Memory:"):
            continue
        if tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def compute_plan_diff(
    prior: WeekPlan | None | dict | object,
    proposed: WeekPlan | None | dict | object,
    *,
    user_msg: str = "",
    citations: list | None = None,
    as_of: date | None = None,
) -> PlanDiff:
    """Diff prior (persisted/checkpoint) vs proposed_week_plan.

    - Duration / focus-core / status changes are first-class.
    - Detail-only focus rewrites (same core name, longer exercise list) are
      kept but marked secondary unless the user named that day.
    - ``requested`` is true when the day matches a relative/named day in
      ``user_msg``, or when duration was asked and that day alone changed duration.
    """
    prior_plan = coerce_week_plan(prior)
    proposed_plan = coerce_week_plan(proposed)
    is_first = prior_plan is None or not (prior_plan.days or [])

    if proposed_plan is None:
        return PlanDiff(
            is_first_plan=is_first,
            memory_tags=memory_tags_from_citations(citations),
        )

    old_map = _day_map(prior_plan)
    new_map = _day_map(proposed_plan)
    all_keys = list(dict.fromkeys([*old_map.keys(), *new_map.keys()]))

    requested_keys = _requested_day_keys(user_msg, as_of=as_of)
    asked_dur = _requested_duration(user_msg)

    changes: list[DayChange] = []
    for key in all_keys:
        old = old_map.get(key)
        new = new_map.get(key)
        kind = _classify(old, new)
        if kind is None:
            continue
        # Drop rest↔rest micro-diffs and removed rest days — "trimmed Rest to
        # 0 minutes" is meaningless noise in the user-facing summary.
        if _is_noise_rest_change(old, new):
            continue
        label = _weekday_label(proposed_plan or prior_plan, key, new or old)
        requested = key in requested_keys
        if (
            not requested
            and asked_dur is not None
            and kind in {"duration", "mixed"}
            and new is not None
            and int(new.duration_min) == asked_dur
        ):
            requested = True
        changes.append(
            DayChange(
                day_abbr=(new.day if new else old.day) if (new or old) else key.title(),
                weekday_full=label,
                kind=kind,
                old=old,
                new=new,
                requested=requested,
            )
        )

    # If nothing was marked requested but exactly one substantive
    # (duration/mixed) change exists, treat that as the requested change.
    if changes and not any(c.requested for c in changes):
        substantive = [
            c for c in changes if c.kind in {"duration", "mixed", "added", "removed"}
        ]
        if len(substantive) == 1:
            only = substantive[0]
            changes = [
                DayChange(
                    day_abbr=c.day_abbr,
                    weekday_full=c.weekday_full,
                    kind=c.kind,
                    old=c.old,
                    new=c.new,
                    requested=(c.day_abbr == only.day_abbr and c.kind == only.kind),
                )
                for c in changes
            ]

    return PlanDiff(
        is_first_plan=is_first,
        changes=changes,
        memory_tags=memory_tags_from_citations(citations),
    )


def _session_label(change: DayChange) -> str:
    focus = change.new_focus or change.old_focus or "session"
    core = _FOCUS_CORE_RE.sub("", focus).strip() or focus
    core = re.sub(r"\[.*?\]", "", core)
    # Drop trailing parentheticals like "(30-min express)" so we don't emit
    # "Upper B (30 to **30 minutes**".
    core = re.sub(r"\s*\([^)]*\)\s*", " ", core)
    core = re.sub(r"\s+", " ", core).strip() or "session"
    if len(core) > 48:
        core = core[:45].rstrip() + "…"
    return core


def format_plan_diff_reply(
    diff: PlanDiff,
    *,
    modes: list[str] | None = None,
    goal: str = "fitness",
) -> str:
    """Compose the concrete plan_changed chat body from a PlanDiff."""
    mode_bit = ", ".join(m for m in (modes or []) if m) or "your preferred training"
    goal_bit = (goal or "fitness").strip()

    if diff.is_first_plan:
        # First plan: keep a clear first-week framing (approval card holds days).
        # Do not enumerate every "added" day — that recreates the day-by-day dump.
        body = (
            f"I've built your first week around {mode_bit} for your {goal_bit} goal, "
            "with workouts and meals ready for you to review."
        )
        if diff.memory_tags:
            body = f"{body}\n\n{' '.join(diff.memory_tags[:2])}"
        return f"{body}\n\nHere's your plan — take a look below."

    requested = list(diff.requested)
    if not requested:
        requested = [
            c
            for c in diff.changes
            if c.kind in {"duration", "mixed", "added", "removed"}
        ][:1]
    secondary = [c for c in diff.changes if c not in requested]

    parts: list[str] = []

    if requested:
        bullets: list[str] = []
        for c in requested:
            # Workout → rest day: never "trimmed … to 0 minutes".
            if _is_rest_day(c.new) and int(c.new_duration or 0) == 0:
                if _is_rest_day(c.old):
                    bullets.append(
                        f"I've kept {c.weekday_full} as a rest day."
                    )
                else:
                    bullets.append(
                        f"I've set {c.weekday_full} as a rest day."
                    )
                continue
            label = _session_label(c)
            if c.kind in {"duration", "mixed"} and c.new_duration is not None:
                if c.old_duration is not None and c.new_duration < c.old_duration:
                    bullets.append(
                        f"I've trimmed {c.weekday_full}'s {label} to "
                        f"**{c.new_duration} minutes**."
                    )
                else:
                    bullets.append(
                        f"I've set {c.weekday_full}'s {label} to "
                        f"**{c.new_duration} minutes**."
                    )
            elif c.kind == "added" and c.new is not None:
                if _is_rest_day(c.new) and int(c.new_duration or 0) == 0:
                    bullets.append(
                        f"I've kept {c.weekday_full} as a rest day."
                    )
                else:
                    bullets.append(
                        f"I've added {c.weekday_full}'s **{label}** "
                        f"({c.new_duration} min)."
                    )
            elif c.kind == "removed":
                if _is_rest_day(c.old):
                    continue  # never "removed Tuesday's Rest"
                bullets.append(f"I've removed {c.weekday_full}'s {label}.")
            else:
                bullets.append(
                    f"I've updated {c.weekday_full}'s session to **{label}**."
                )
        if bullets:
            parts.append(" ".join(bullets))
        else:
            parts.append(
                f"I've adjusted this week around {mode_bit} while keeping your "
                f"{goal_bit} goal in mind."
            )
    else:
        parts.append(
            f"I've adjusted this week around {mode_bit} while keeping your "
            f"{goal_bit} goal in mind."
        )

    if secondary:
        names = list(dict.fromkeys(c.weekday_full for c in secondary[:4]))
        if len(names) == 1:
            day_bit = names[0]
        elif len(names) == 2:
            day_bit = f"{names[0]} and {names[1]}"
        else:
            day_bit = ", ".join(names[:-1]) + f", and {names[-1]}"
        parts.append(
            f"I also refreshed exercise detail on {day_bit} to stay "
            f"aligned with your preferences — the approval card has the full week."
        )

    if diff.memory_tags:
        parts.append(" ".join(diff.memory_tags[:2]))

    parts.append("Here's the update — take a look below.")
    return "\n\n".join(parts)

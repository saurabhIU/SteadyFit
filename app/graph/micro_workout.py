"""Deterministic \"I have 10 minutes\" micro-workout + Done logging.

No council critique / HITL — fast path only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.graph.plan_utils import date_for_weekday
from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.memory.store import get_saved_week_plan, log_workout, save_week_plan

TEN_MINUTE_CHIP = "I have 10 minutes"
DONE_CHIP = "done"
REPLACE_CHIP = "Replace today's session"
EXTRA_CHIP = "Log as extra"
QUICK_SOURCE = "quick_10min"
QUICK_FOCUS = "10-min quick session"

SOFT_PREF_LINE = (
    "Want me to remember your preferences for next time? Tell me your goal anytime."
)

TodayCase = Literal["no_plan", "rest", "planned_pending", "planned_done"]

_TEN_MIN_RE = re.compile(
    r"(?is)\b("
    r"i\s+(?:only\s+)?have\s+(?:only\s+)?(?:10|ten)\s+min(?:ute)?s?"
    r"|only\s+(?:10|ten)\s+min(?:ute)?s?"
    r"|got\s+(?:10|ten)\s+min(?:ute)?s?"
    r"|(?:10|ten)[\s-]?min(?:ute)?\s+workout"
    r"|quick\s+(?:10|ten)[\s-]?min"
    r")\b"
)

_DONE_RE = re.compile(r"(?is)^\s*(done|finished|all done|logged)\s*[.!?]?\s*$")


def looks_like_ten_minute_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw.lower() == TEN_MINUTE_CHIP.lower():
        return True
    return bool(_TEN_MIN_RE.search(raw))


def looks_like_quick_10_done(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if raw.lower() == DONE_CHIP:
        return True
    return bool(_DONE_RE.match(raw))


def looks_like_quick_10_replace(text: str) -> bool:
    t = (text or "").strip().lower()
    return t == REPLACE_CHIP.lower() or t.startswith("replace today")


def looks_like_quick_10_extra(text: str) -> bool:
    t = (text or "").strip().lower()
    return t == EXTRA_CHIP.lower() or t in {"log as extra", "extra", "keep both"}


def _modes(profile: UserProfile) -> set[str]:
    return {m.strip().lower() for m in (profile.preferred_workout_modes or []) if m}


def _constraint_blob(profile: UserProfile) -> str:
    return " ".join(profile.constraints or []).lower()


def modality_known(profile: UserProfile) -> bool:
    return bool(_modes(profile))


@dataclass(frozen=True)
class TodayPlanContext:
    """Which of the four Done cases applies for ``as_of``."""

    case: TodayCase
    week_plan: WeekPlan | None
    today_day: WorkoutDay | None
    today_iso: str


def resolve_today_plan_context(
    week_plan: WeekPlan | None,
    *,
    as_of: date | None = None,
) -> TodayPlanContext:
    """Single date source of truth: week_start (Mon) + weekday offset == today.

    Cases:
      no_plan         — no WeekPlan (or empty days)
      rest            — plan exists but today has no planned session / skipped
      planned_pending — today has a session not yet done
      planned_done    — today's planned session already marked done
    """
    today = as_of or date.today()
    today_iso = today.isoformat()
    if not week_plan or not week_plan.days:
        return TodayPlanContext("no_plan", week_plan, None, today_iso)

    today_day: WorkoutDay | None = None
    for day in week_plan.days:
        day_date = date_for_weekday(week_plan.week_start, day.day)
        if day_date == today:
            today_day = day
            break

    if today_day is None or today_day.status == "skipped":
        return TodayPlanContext("rest", week_plan, today_day, today_iso)
    if today_day.status == "done":
        return TodayPlanContext("planned_done", week_plan, today_day, today_iso)
    # planned or moved → still outstanding for today
    return TodayPlanContext("planned_pending", week_plan, today_day, today_iso)


def build_ten_minute_reply(profile: UserProfile) -> str:
    """Concrete 10-minute session adapted to modes + injury constraints."""
    modes = _modes(profile)
    blob = _constraint_blob(profile)
    knee = "knee" in blob
    shoulder = "shoulder" in blob
    name = (profile.name or "").strip() or "there"

    if knee:
        blocks = [
            ("0:00–1:00", "Easy march in place + ankle circles (warm joints)."),
            ("1:00–4:00", "Sit-to-stand from a chair × 8–10, slow and controlled."),
            ("4:00–7:00", "Glute bridge × 10 + side-lying clam × 8/side (no deep knee bend)."),
            ("7:00–9:30", "Brisk walk or easy cycle if you have one — keep knees happy."),
            ("9:30–10:00", "Slow breathing, 4 counts in / 6 out."),
        ]
        caveat = "Knee-aware picks — stop if anything sharp shows up."
    elif shoulder:
        blocks = [
            ("0:00–1:00", "Arm circles + scap squeezes (gentle)."),
            ("1:00–4:00", "Bodyweight squats × 10 + hip hinge good-mornings × 8."),
            ("4:00–7:00", "Glute bridge × 12 + dead bug × 6/side (arms only as high as comfy)."),
            ("7:00–9:30", "Brisk march or walk — keep shoulders relaxed."),
            ("9:30–10:00", "Doorway chest stretch, easy."),
        ]
        caveat = "Shoulder-aware — skip anything that pinches overhead."
    elif modes & {"walking", "running"} and not (modes & {"gym", "home"}):
        blocks = [
            ("0:00–1:00", "Easy walk to wake up."),
            ("1:00–8:00", "Brisk walk (or light jog if that feels normal for you)."),
            ("8:00–9:30", "4×20s faster pace / 20s easy."),
            ("9:30–10:00", "Slow walk + shoulder rolls."),
        ]
        caveat = "Outdoor or hallway — shoes on, nothing fancy."
    elif "swimming" in modes and not (modes & {"gym", "home", "walking"}):
        blocks = [
            ("0:00–1:00", "Easy splash / arm swings on deck."),
            ("1:00–8:00", "Continuous easy swim — whatever stroke feels good."),
            ("8:00–9:30", "4×20s a bit quicker / 20s easy."),
            ("9:30–10:00", "Float or slow kick to cool down."),
        ]
        caveat = "Pool session — keep it conversational pace."
    elif "yoga" in modes and "gym" not in modes:
        blocks = [
            ("0:00–1:00", "Cat-cow × 6."),
            ("1:00–4:00", "Down-dog → plank walkouts × 5."),
            ("4:00–7:00", "Chair pose hold 20s × 3 + glute bridge × 10."),
            ("7:00–9:30", "World's greatest stretch × 3/side."),
            ("9:30–10:00", "Child's pose, breathe."),
        ]
        caveat = "Mat or carpet is enough."
    elif "gym" in modes:
        blocks = [
            ("0:00–1:00", "Easy bike or march 60s."),
            ("1:00–4:00", "Goblet or bodyweight squat × 8 + push-up (or incline) × 6."),
            ("4:00–7:00", "Hip hinge / RDL pattern × 8 + row or band pull-apart × 10."),
            ("7:00–9:30", "Farmer carry or brisk walk 90s + dead bug × 6/side."),
            ("9:30–10:00", "Easy breathe-down."),
        ]
        caveat = "Light load — this is a keep-the-streak-alive session, not a PR day."
    else:
        # home / mixed / unspecified → bodyweight default
        blocks = [
            ("0:00–1:00", "Jumping jacks or march × 60s."),
            ("1:00–4:00", "Bodyweight squat × 10 + push-up (knees OK) × 6."),
            ("4:00–7:00", "Reverse lunge × 6/side + glute bridge × 12."),
            ("7:00–9:30", "Plank 20s × 2 + mountain climbers 20s."),
            ("9:30–10:00", "Shake out + 3 slow breaths."),
        ]
        caveat = "No equipment — living room works."

    lines = [
        f"Got it, {name} — **10 minutes is enough.** Here's a tight session "
        f"you can start now ({caveat})",
        "",
    ]
    for clock, move in blocks:
        lines.append(f"- **{clock}** — {move}")
    lines.extend(
        [
            "",
            f'When you\'re done, tap **{DONE_CHIP}** — no guilt if you only get '
            "partway. A short session still moves the week forward.",
        ]
    )
    return "\n".join(lines)


def _soft_pref_suffix(profile: UserProfile) -> str:
    if modality_known(profile):
        return ""
    return f"\n\n{SOFT_PREF_LINE}"


def _mark_today_done(plan: WeekPlan, today: date) -> WeekPlan:
    new_days: list[WorkoutDay] = []
    for day in plan.days:
        day_date = date_for_weekday(plan.week_start, day.day)
        if day_date == today:
            new_days.append(day.model_copy(update={"status": "done"}))
        else:
            new_days.append(day)
    return plan.model_copy(update={"days": new_days})


@dataclass
class Quick10LogResult:
    reply: str
    quick_replies: list[str]
    week_plan: WeekPlan | None = None
    awaiting_choice: bool = False
    logged: bool = False


def handle_quick_10_done(
    *,
    user_id: str,
    profile: UserProfile,
    week_plan: WeekPlan | None,
    as_of: date | None = None,
) -> Quick10LogResult:
    """Log the quick session; prompt only when today has a pending planned day."""
    today = as_of or date.today()
    plan = week_plan or (get_saved_week_plan(user_id) if user_id else None)
    ctx = resolve_today_plan_context(plan, as_of=today)

    log_workout(
        user_id,
        ctx.today_iso,
        QUICK_FOCUS,
        "done",
        source=QUICK_SOURCE,
    )

    soft = _soft_pref_suffix(profile)

    if ctx.case == "planned_pending":
        return Quick10LogResult(
            reply=(
                "Logged your 10-minute session — nice work.\n\n"
                "Count this as today's session, or log it separately and keep "
                "today's planned workout too?"
                f"{soft}"
            ),
            quick_replies=[REPLACE_CHIP, EXTRA_CHIP],
            week_plan=plan,
            awaiting_choice=True,
            logged=True,
        )

    # no_plan / rest / planned_done — confirm, no conflict prompt
    return Quick10LogResult(
        reply=f"Logged your 10-minute session — nice work.{soft}",
        quick_replies=[],
        week_plan=plan,
        awaiting_choice=False,
        logged=True,
    )


def handle_quick_10_choice(
    *,
    user_id: str,
    profile: UserProfile,
    week_plan: WeekPlan | None,
    choice: Literal["replace", "extra"],
    as_of: date | None = None,
) -> Quick10LogResult:
    """Resolve replace-vs-extra after Done already wrote workout_log."""
    today = as_of or date.today()
    plan = week_plan or (get_saved_week_plan(user_id) if user_id else None)
    soft = _soft_pref_suffix(profile)

    if choice == "replace" and plan is not None:
        updated = _mark_today_done(plan, today)
        save_week_plan(user_id, updated)
        return Quick10LogResult(
            reply=(
                "Got it — today's planned session is marked done via your "
                f"10-minute workout. Nice work.{soft}"
            ),
            quick_replies=[],
            week_plan=updated,
            awaiting_choice=False,
            logged=False,
        )

    return Quick10LogResult(
        reply=(
            "Got it — your 10-minute session stays as a bonus. Today's planned "
            f"workout is still waiting whenever you're ready.{soft}"
        ),
        quick_replies=[],
        week_plan=plan,
        awaiting_choice=False,
        logged=False,
    )

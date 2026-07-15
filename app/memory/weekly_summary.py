"""Weekly coaching-memory summarization (facts only → compact embed text)."""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, Field

from app.config import get_llm, settings
from app.graph.state import WeekPlan
from app.memory.store import get_adherence_stats, get_saved_week_plan, get_workouts_between
from app.security import as_text, wrap_untrusted
from langsmith import traceable

logger = logging.getLogger("steadyfit.memory")

SUMMARIZER_SYSTEM = """You are SteadyFit's weekly coaching-memory writer.
Given structured facts about ONE completed training week, fill the WeeklySummary schema.

Include ONLY facts present in the provided data (plan days/statuses, workout logs,
adherence stats, specialist/council proposal notes, and user chat messages).
Do not invent events, emotions, diagnoses, or motives.
Do not moralize: a skipped session is a logged status, not a failure narrative.
Neutral, concrete language. Prefer short sentences.
context_tags: 0–6 lowercase snake_case labels that appear in the data
(e.g. travel, hotel_gym, high_work_stress, illness, simplified_plan).
If a field has no supporting evidence, write "none noted".
Target length when the fields are later rendered: about 150–250 words total."""


class WeeklySummary(BaseModel):
    """Structured coaching-memory record for one ISO week (facts only)."""

    week_start: date
    context_tags: list[str] = Field(
        default_factory=list,
        description='Short labels present in the week data, e.g. ["travel", "hotel_gym"].',
    )
    planned_vs_done: str = Field(
        description='Attendance vs plan, e.g. "4 planned, 3 done, 1 moved to Sat".',
    )
    what_worked: str = Field(
        description="Concrete things that went as planned or helped adherence.",
    )
    what_didnt: str = Field(
        description="Misses, moves, conflicts, meals-of-note that disrupted the plan.",
    )
    council_adjustments: str = Field(
        description="Plan changes and why (e.g. risk flag → simplified sessions).",
    )
    user_signals: str = Field(
        description="Energy/mood/constraints the user explicitly said — stated facts only.",
    )

    def to_embed_text(self) -> str:
        tags = ", ".join(self.context_tags) if self.context_tags else "none"
        return (
            f"Week of {self.week_start.isoformat()}\n"
            f"Context tags: {tags}\n"
            f"Planned vs done: {self.planned_vs_done}\n"
            f"What worked: {self.what_worked}\n"
            f"What didn't: {self.what_didnt}\n"
            f"Council adjustments: {self.council_adjustments}\n"
            f"User signals: {self.user_signals}\n"
        )


def iso_week_start(d: date | None = None) -> date:
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def previous_week_start(as_of: date | None = None) -> date:
    """Week that just completed when running a Sunday review."""
    return iso_week_start(as_of) - timedelta(days=7)


def gather_week_facts(
    week_start: date,
    *,
    user_id: str,
    week_plan: WeekPlan | None = None,
    proposals: dict | None = None,
    user_messages: list[str] | None = None,
    risk_flag: bool = False,
) -> dict[str, Any]:
    """Collect structured inputs for the summarizer (no LLM)."""
    plan = week_plan or get_saved_week_plan(user_id)
    end = week_start + timedelta(days=7)
    workouts = get_workouts_between(user_id, week_start, end)
    stats = get_adherence_stats(user_id)
    plan_days = []
    if plan and plan.week_start[:10] == week_start.isoformat():
        plan_days = [d.model_dump() for d in plan.days]
    return {
        "week_start": week_start.isoformat(),
        "user_id": user_id,
        "week_plan_days": plan_days,
        "week_plan_notes": (plan.notes if plan else "") or "",
        "workout_logs": workouts,
        "adherence_stats": stats,
        "risk_flag": risk_flag,
        "council_proposals": {
            k: (v[:800] if isinstance(v, str) else v)
            for k, v in (proposals or {}).items()
            if k in {"scheduler", "adherence", "nutrition", "knowledge"}
            or k.endswith("_summary")
        },
        "user_messages": list(user_messages or [])[:20],
    }


@traceable(name="weekly_summary", run_type="chain")
def generate_weekly_summary(
    week_start: date,
    *,
    user_id: str,
    week_plan: WeekPlan | None = None,
    proposals: dict | None = None,
    user_messages: list[str] | None = None,
    risk_flag: bool = False,
) -> WeeklySummary:
    """LLM structured summary for one week (cheap judge model)."""
    facts = gather_week_facts(
        week_start,
        user_id=user_id,
        week_plan=week_plan,
        proposals=proposals,
        user_messages=user_messages,
        risk_flag=risk_flag,
    )
    llm = get_llm(settings.judge_model, temperature=0, max_tokens=700)
    structured = llm.with_structured_output(WeeklySummary)
    payload = wrap_untrusted(json.dumps(facts, default=str), source="week_facts")
    result = structured.invoke([
        {"role": "system", "content": SUMMARIZER_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Summarize the week starting {week_start.isoformat()}.\n\n{payload}"
            ),
        },
    ])
    if isinstance(result, WeeklySummary):
        # Force week_start from input (model may drift).
        return result.model_copy(update={"week_start": week_start})
    # Fallback if wrapper returns dict-like
    data = result if isinstance(result, dict) else {}
    data["week_start"] = week_start
    return WeeklySummary(**data)


def fallback_summary_from_facts(
    week_start: date,
    facts: dict[str, Any] | None = None,
    *,
    user_id: str | None = None,
) -> WeeklySummary:
    """Deterministic summary when the LLM is unavailable (backfill / tests)."""
    if facts is None:
        if not user_id:
            raise ValueError("user_id required when facts omitted")
        facts = gather_week_facts(week_start, user_id=user_id)
    logs = facts.get("workout_logs") or []
    by_status: dict[str, int] = {}
    for row in logs:
        st = row.get("status") or "unknown"
        by_status[st] = by_status.get(st, 0) + 1
    planned = len(facts.get("week_plan_days") or []) or sum(by_status.values())
    done = by_status.get("done", 0)
    skipped = by_status.get("skipped", 0)
    moved = by_status.get("moved", 0)
    tags: list[str] = []
    notes = (facts.get("week_plan_notes") or "").lower()
    for label, needles in [
        ("travel", ("travel", "hotel")),
        ("hotel_gym", ("hotel",)),
        ("simplified_plan", ("simplif", "shorter")),
        ("high_work_stress", ("work", "overwhelm", "busy")),
        ("illness", ("sick", "ill")),
    ]:
        blob = notes + " " + " ".join(str(m) for m in facts.get("user_messages") or [])
        if any(n in blob for n in needles):
            tags.append(label)
    if facts.get("risk_flag"):
        tags.append("risk_flag")
    return WeeklySummary(
        week_start=week_start,
        context_tags=tags[:6],
        planned_vs_done=(
            f"{planned} planned, {done} done, {skipped} skipped, {moved} moved"
        ),
        what_worked=("Completed sessions logged." if done else "none noted"),
        what_didnt=(
            f"{skipped} skipped sessions in logs." if skipped else "none noted"
        ),
        council_adjustments=(
            "Risk flag was set during coaching."
            if facts.get("risk_flag")
            else "none noted"
        ),
        user_signals=(
            "; ".join(str(m)[:120] for m in (facts.get("user_messages") or [])[:3])
            or "none noted"
        ),
    )


def extract_user_texts(messages: list) -> list[str]:
    out: list[str] = []
    for m in messages or []:
        role = getattr(m, "type", None) or (m.get("role") if isinstance(m, dict) else None)
        if role in {"human", "user"}:
            content = getattr(m, "content", None)
            if content is None and isinstance(m, dict):
                content = m.get("content")
            text = as_text(content)
            if text and "SYSTEM_TRIGGER" not in text:
                out.append(text)
    return out

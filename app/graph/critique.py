"""Pre-merge critique-and-revise for plan-changing specialist drafts.

Separate from the post-merge risk_flag renegotiation loop (coaching_team_rounds).
Cap: at most one revise cycle per specialist per turn (critique_rounds).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from langsmith import traceable

from app.config import get_llm, settings
from app.graph.state import CoachingTeamState
from app.security import (
    as_text,
    looks_like_topic_interrupt,
    with_security,
    wrap_untrusted,
)

logger = logging.getLogger(__name__)

MAX_CRITIQUE_ROUNDS = 1

SPECIALIST_KEYS = ("scheduler", "nutrition", "adherence", "knowledge")

CRITIQUE_SYSTEM = """You are the Coach co-lead doing a fast quality check on ONE specialist draft
before it is merged into the user reply. Be strict but brief.

Check ONLY these failure modes:
1) Contradicts a KB contraindication or known constraint (injuries, equipment limits).
2) Ignores an explicit profile fact (food preference, sessions/week, goal).
3) Volume/intensity unrealistic for the user's experience level (e.g. beginner → advanced program).
4) Makes a specific factual claim (macro target, exercise safety) with no KB/memory citation in the draft or context.

Output JSON only:
{"verdict":"clean"}
OR
{"verdict":"revise","critique":"<one specific actionable critique, max 2 sentences>"}

If multiple issues exist, pick the single most important one.

DEFAULT TO "clean". Only choose "revise" for a CLEAR, unambiguous failure, such as:
- named injury/constraint vs a named contraindicated movement in the draft
- sessions_per_week explicitly mismatched (e.g. profile=3 but draft schedules 6 hard sessions)
- vegan/vegetarian profile but draft requires excluded animal foods
- beginner given an advanced high-volume program

Do NOT revise for subjective nits: calorie preference tweaks, protein targets that are
achievable for the food preference, missing meal examples, tone, or optional improvements.

NEVER flag or soften a safety-relevant acknowledgment (pain/injury, allergy, pregnancy).
If the draft correctly prioritizes a safety interrupt over completing a prior workout/meal
plan, that is SUCCESS — output {"verdict":"clean"}. Do not ask the specialist to "finish
the original plan" instead.

If unsure, output {"verdict":"clean"}."""


def active_specialist(state: CoachingTeamState) -> str | None:
    """Which specialist wrote the draft currently under review."""
    for key in SPECIALIST_KEYS:
        if key in state.proposals and state.proposals.get(key):
            # Prefer the specialist matching intent when multiple keys linger.
            intent = (state.intent or "").lower()
            if intent in {"schedule", "first_plan"} and key == "scheduler":
                return key
            if intent == "nutrition" and key == "nutrition":
                return key
            if intent == "adherence" and key == "adherence":
                return key
            if intent == "knowledge" and key == "knowledge":
                return key
    for key in SPECIALIST_KEYS:
        val = state.proposals.get(key)
        if isinstance(val, str) and val.strip():
            return key
    return None


def looks_like_nutrition_plan_change(text: str) -> bool:
    """Heuristic: nutrition draft proposes macro/meal-plan adjustments."""
    t = (text or "").lower()
    markers = (
        "protein", "calorie", "kcal", "macro", "g/day", "g per day",
        "target", "meal plan", "remaining", "adjust", "aim for",
    )
    return sum(1 for m in markers if m in t) >= 2


def should_critique(state: CoachingTeamState) -> bool:
    """Only plan-changing turns — skip knowledge, adherence check-ins, and interrupts.

    Safety interrupts (pain/allergy/pregnancy) are acknowledgments, not draft plans to
    optimize — critique must not second-guess them (same skip path as pure knowledge).
    """
    user_msg = as_text(state.messages[-1].content) if state.messages else ""
    if looks_like_topic_interrupt(user_msg):
        return False

    intent = (state.intent or "").lower()
    if intent in {"schedule", "first_plan"}:
        return True
    if state.proposals.get("plan_changed"):
        return True
    if intent == "nutrition":
        if state.proposals.get("nutrition_plan_change"):
            return True
        draft = str(state.proposals.get("nutrition") or "")
        return looks_like_nutrition_plan_change(draft)
    return False


def route_after_specialist(state: CoachingTeamState) -> str:
    if should_critique(state):
        return "critique"
    return "coaching_team"


def route_from_critique(state: CoachingTeamState) -> str:
    """After critique: revise once via the same specialist, else merge.

    critique_rounds is incremented when a revision is requested. As long as
    revision_instructions are present, route back to the specialist; the
    critique node clears those instructions on the post-revision pass
    (capped — no second revise).
    """
    if state.proposals.get("revision_instructions"):
        return active_specialist(state) or "scheduler"
    return "coaching_team"


def _excerpt(text: str, limit: int = 400) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _parse_critique(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {"verdict": "clean"}


def revision_block(state: CoachingTeamState) -> str:
    """Append to specialist prompts when a critique requested a rewrite."""
    note = state.proposals.get("revision_instructions")
    if not note:
        return ""
    return (
        f"\n\nYour council co-lead flagged: {note} "
        "Revise your proposal to address this. Keep the same overall intent; "
        "fix only the flagged issue.\n"
    )


@traceable(name="council_critique", run_type="chain")
def _run_critique_llm(
    *,
    specialist: str,
    draft: str,
    profile_json: str,
    constraints: list[str],
    retrieved_context: str,
) -> dict[str, Any]:
    llm = get_llm(settings.judge_model, temperature=0, max_tokens=120)
    user = (
        f"User profile (facts you must respect):\n{profile_json}\n\n"
        f"Known constraints / injuries: {constraints or 'none'}\n\n"
        f"Retrieved context / KB snippets (may be empty):\n"
        f"{retrieved_context or 'none'}\n\n"
        f"Specialist that drafted: {specialist}\n"
        f"Draft proposal:\n{wrap_untrusted(draft, source=f'proposal:{specialist}')}\n"
    )
    raw = as_text(
        llm.invoke(
            [
                {"role": "system", "content": with_security(CRITIQUE_SYSTEM)},
                {"role": "user", "content": user},
            ]
        ).content
    )
    parsed = _parse_critique(raw)
    verdict = str(parsed.get("verdict") or "clean").strip().lower()
    if verdict not in {"clean", "revise"}:
        verdict = "clean"
    critique = str(parsed.get("critique") or "").strip()
    if verdict == "revise" and not critique:
        verdict = "clean"
    revision_triggered = verdict == "revise"
    # Explicit fields for LangSmith / eval visibility.
    return {
        "verdict": verdict,
        "critique": critique,
        "revision_triggered": revision_triggered,
        "specialist": specialist,
    }


def _looks_like_hard_failure(critique: str) -> bool:
    """Reject soft nitpicks so clean drafts don't burn a revise cycle."""
    t = (critique or "").lower()
    hard = (
        "constraint", "contraindic", "injury", "knee", "shoulder", "wrist", "back pain",
        "sessions_per_week", "sessions per week", "too many session", "too few session",
        "beginner", "advanced", "vegan", "vegetarian diet but", "allergy", "equipment",
        "ignores", "contradict", "unsafe",
    )
    return any(s in t for s in hard)


def critique_node(state: CoachingTeamState) -> dict:
    specialist = active_specialist(state)
    if not specialist:
        return {"critique_verdict": "skipped"}

    draft = str(state.proposals.get(specialist) or "")
    transcript = list(state.coaching_team_transcript or [])
    proposals = dict(state.proposals)

    # Already used the one allowed revise cycle — record revised draft and merge
    # without another LLM call (bounded latency/cost).
    if state.critique_rounds >= MAX_CRITIQUE_ROUNDS:
        if any(e.get("type") == "critique" for e in transcript):
            transcript.append({
                "type": "revision",
                "agent": specialist,
                "text": _excerpt(draft),
            })
        proposals.pop("revision_instructions", None)
        logger.info(
            "council_critique capped specialist=%s rounds=%s → merge",
            specialist,
            state.critique_rounds,
        )
        return {
            "proposals": proposals,
            "coaching_team_transcript": transcript,
            "critique_verdict": "revise_capped",
            "critique_rounds": state.critique_rounds,
        }

    context = "\n\n".join(state.retrieved_context[:6]) if state.retrieved_context else ""
    try:
        out = _run_critique_llm(
            specialist=specialist,
            draft=draft,
            profile_json=state.profile.model_dump_json(),
            constraints=list(state.profile.constraints or []),
            retrieved_context=context,
        )
    except Exception as exc:
        logger.warning("council_critique_error falling_clean err=%s", exc)
        out = {
            "verdict": "clean",
            "critique": "",
            "revision_triggered": False,
            "specialist": specialist,
        }

    verdict = out["verdict"]
    critique = str(out.get("critique") or "").strip()
    # Soft-nitpick guard: protein/calorie preference tweaks must not force revise.
    if verdict == "revise" and not _looks_like_hard_failure(critique):
        logger.info(
            "council_critique soft_nitpick_coerced_clean specialist=%s critique=%r",
            specialist,
            critique[:160],
        )
        verdict = "clean"
        out = {**out, "verdict": "clean", "revision_triggered": False}

    if verdict == "clean":
        proposals.pop("revision_instructions", None)
        logger.info(
            "council_critique verdict=clean specialist=%s revision_triggered=False",
            specialist,
        )
        return {
            "proposals": proposals,
            "critique_verdict": "clean",
            "critique_rounds": state.critique_rounds,
        }

    transcript.append({
        "type": "proposal",
        "agent": specialist,
        "text": _excerpt(draft),
    })
    transcript.append({
        "type": "critique",
        "agent": "coach",
        "text": critique,
    })
    proposals["revision_instructions"] = critique
    logger.info(
        "council_critique verdict=revise specialist=%s revision_triggered=True",
        specialist,
    )
    return {
        "proposals": proposals,
        "coaching_team_transcript": transcript,
        "critique_verdict": "revise",
        # Mark that one revise cycle is in flight / consumed.
        "critique_rounds": state.critique_rounds + 1,
    }

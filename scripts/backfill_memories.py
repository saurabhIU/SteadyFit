"""Generate coaching-memory rows from workout history + optional demo seeds.

  uv run python scripts/backfill_memories.py --user-id demo-veteran
  uv run python scripts/backfill_memories.py --user-id demo-veteran --seed-demo
  uv run python scripts/backfill_memories.py --user-id demo-veteran --no-llm

Requires DATABASE_URL + OPENAI_API_KEY (embeddings). LLM summarizer needs AI_GATEWAY_API_KEY
unless --no-llm.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

from app.memory.store import list_users, list_workout_week_starts, user_exists  # noqa: E402
from app.memory.weekly_summary import (  # noqa: E402
    WeeklySummary,
    fallback_summary_from_facts,
    gather_week_facts,
    generate_weekly_summary,
)
from app.rag.memory_store import upsert_weekly_memory  # noqa: E402


def seed_demo_memories(user_id: str) -> list[str]:
    """Two synthetic past weeks for memory evals / demos."""
    today = date.today()
    travel_week = today - timedelta(days=today.weekday() + 28)  # ~4 weeks ago
    overload_week = today - timedelta(days=today.weekday() + 14)  # ~2 weeks ago

    travel = WeeklySummary(
        week_start=travel_week,
        context_tags=["travel", "hotel_gym"],
        planned_vs_done="3 planned, 3 done (all hotel sessions), 0 skipped",
        what_worked=(
            "Short 3×20-min hotel sessions (push-up chest_010, band row, goblet squat) "
            "completed every planned day."
        ),
        what_didnt="none noted",
        council_adjustments=(
            "Switched barbell gym plan to hotel bodyweight; kept three short sessions."
        ),
        user_signals="User said travel week with hotel gym only; energy felt steady.",
    )
    overload = WeeklySummary(
        week_start=overload_week,
        context_tags=["high_work_stress", "simplified_plan", "risk_flag"],
        planned_vs_done="5 planned, 2 done, 3 skipped",
        what_worked="Two short walks completed mid-week.",
        what_didnt="Three gym sessions skipped after consecutive late workdays.",
        council_adjustments=(
            "Adherence flagged RISK; council simplified next week to 3 shorter sessions."
        ),
        user_signals="User said work was crazy and felt overwhelmed.",
    )
    return [
        upsert_weekly_memory(travel, user_id),
        upsert_weekly_memory(overload, user_id),
    ]


def backfill_from_logs(user_id: str, *, use_llm: bool) -> list[str]:
    written: list[str] = []
    for week_start in list_workout_week_starts(user_id):
        try:
            if use_llm:
                summary = generate_weekly_summary(week_start, user_id=user_id)
            else:
                summary = fallback_summary_from_facts(
                    week_start, gather_week_facts(week_start, user_id=user_id)
                )
            written.append(upsert_weekly_memory(summary, user_id))
            print(f"  ok {user_id} {week_start.isoformat()}")
        except Exception as exc:
            print(f"  fail {user_id} {week_start.isoformat()}: {exc}", file=sys.stderr)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill coaching memories into pgvector")
    parser.add_argument(
        "--user-id",
        default=None,
        help="Profile to backfill (default: all app_users)",
    )
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Upsert travel + overload synthetic weeks for demos/evals",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Use deterministic fallback summaries (no gateway calls)",
    )
    parser.add_argument(
        "--skip-logs",
        action="store_true",
        help="Do not scan workout_log weeks",
    )
    args = parser.parse_args()

    if args.user_id:
        if not user_exists(args.user_id):
            sys.exit(f"unknown user_id: {args.user_id}")
        user_ids = [args.user_id]
    else:
        user_ids = [u["user_id"] for u in list_users()]
        if not user_ids:
            sys.exit("No app_users found. Seed profiles first (scripts/seed_memory.py).")

    all_src: list[str] = []
    for uid in user_ids:
        if not args.skip_logs:
            print(f"Backfilling from workout_log for {uid}…")
            all_src.extend(backfill_from_logs(uid, use_llm=not args.no_llm))
        if args.seed_demo:
            print(f"Seeding demo travel + overload memories for {uid}…")
            all_src.extend(seed_demo_memories(uid))
    print(f"Upserted {len(set(all_src))} unique memory source_files ({len(all_src)} writes)")


if __name__ == "__main__":
    main()

"""Seed demo profiles into Neon/Postgres.

  uv run python scripts/seed_memory.py --profile fresh
  uv run python scripts/seed_memory.py --profile veteran --history-weeks 12 --no-llm
  uv run python scripts/seed_memory.py --profile veteran --yes   # required if not localhost
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

from app.config import settings  # noqa: E402
from app.graph.state import UserProfile, WeekPlan, WorkoutDay  # noqa: E402
from app.memory.store import (  # noqa: E402
    ensure_user,
    log_weight,
    log_workout,
    reset_user,
    save_profile,
    save_week_plan,
    user_exists,
)
from app.memory.weekly_summary import WeeklySummary  # noqa: E402
from app.rag.memory_store import upsert_weekly_memory  # noqa: E402

# Current / steady-week template (Mon–Fri).
VETERAN_WEEK_DAYS = (
    ("Mon", "Upper A", 50),
    ("Tue", "Lower A", 50),
    ("Wed", "Conditioning", 35),
    ("Thu", "Upper B", 50),
    ("Fri", "Lower B", 50),
)

FOCUS_POOL = [focus for _, focus, _ in VETERAN_WEEK_DAYS] + [
    "Hotel full body 20m",
    "Walk 30m",
]

# Personal docs used by rag_personal eval cases (demo-veteran).
EVAL_UPLOADS = Path(__file__).resolve().parents[1] / "data" / "eval_uploads"
EVAL_PERSONAL_DOCS = (
    ("my_program.md", "program"),
    ("sample_hypertrophy_basics.md", "reference"),
    ("recipes.md", "recipes"),
    ("personal_notes.md", "personal"),
)


def _seed_personal_docs(uid: str) -> None:
    """Ingest fixture uploads so personal RAG evals have grounded [doc:] sources."""
    from app.rag.ingest import ingest

    if not EVAL_UPLOADS.is_dir():
        print(f"  skip personal docs: missing {EVAL_UPLOADS}")
        return
    dest_dir = Path("data/uploads") / uid
    dest_dir.mkdir(parents=True, exist_ok=True)
    for name, doc_type in EVAL_PERSONAL_DOCS:
        src = EVAL_UPLOADS / name
        if not src.exists():
            print(f"  skip missing fixture {name}")
            continue
        dest = dest_dir / name
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        n = ingest(str(dest), doc_type=doc_type, user_id=uid)
        print(f"  ingested personal doc {name} ({doc_type}): {n} chunks")


def _require_yes_for_remote(yes: bool) -> None:
    url = settings.database_url or ""
    host = urlparse(url).hostname or ""
    print(f"DATABASE_URL host: {host or '(unset)'}")
    if not url:
        sys.exit("DATABASE_URL is not set")
    local = host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local")
    if not local and not yes:
        sys.exit(
            f"Refusing to write to non-localhost host '{host}'. Re-run with --yes to confirm."
        )


def seed_fresh() -> str:
    uid = "demo-new"
    if user_exists(uid):
        reset_user(uid)
    else:
        ensure_user(uid, "Demo New")
    save_profile(
        uid,
        UserProfile(
            name="Demo New",
            goal="",
            onboarding_complete=False,
            awaiting_onboarding_confirm=False,
        ),
    )
    print(f"Seeded FRESH profile {uid} (onboarding_complete=False)")
    return uid


def _template_memory(
    week_start: date,
    *,
    kind: str,
    planned: int,
    done: int,
    skipped: int,
) -> WeeklySummary:
    if kind == "travel":
        return WeeklySummary(
            week_start=week_start,
            context_tags=["travel", "hotel_gym"],
            planned_vs_done=f"{planned} planned, {done} done (hotel), {skipped} skipped",
            what_worked=(
                "Short 3×20-min hotel sessions (push-up chest_010, band row, goblet squat) "
                "completed on planned days."
            ),
            what_didnt="none noted" if skipped == 0 else f"{skipped} sessions skipped",
            council_adjustments=(
                "Switched gym barbell work to hotel bodyweight; kept short sessions."
            ),
            user_signals="User said travel week with hotel gym only.",
        )
    if kind == "bad":
        return WeeklySummary(
            week_start=week_start,
            context_tags=["high_work_stress", "simplified_plan", "risk_flag"],
            planned_vs_done=f"{planned} planned, {done} done, {skipped} skipped",
            what_worked="Two short walks completed mid-week." if done else "none noted",
            what_didnt=f"{skipped} gym sessions skipped after late workdays.",
            council_adjustments=(
                "Adherence flagged RISK; council simplified next week toward fewer/shorter sessions."
            ),
            user_signals="User said work was crazy and felt overwhelmed.",
        )
    return WeeklySummary(
        week_start=week_start,
        context_tags=["steady_week"],
        planned_vs_done=f"{planned} planned, {done} done, {skipped} skipped",
        what_worked=f"{done} sessions completed as planned.",
        what_didnt="none noted" if skipped == 0 else f"{skipped} skips logged",
        council_adjustments="none noted",
        user_signals="none noted",
    )


def seed_veteran(*, history_weeks: int, no_llm: bool) -> str:
    uid = "demo-veteran"
    if user_exists(uid):
        reset_user(uid)
    else:
        ensure_user(uid, "Saurabh")
    save_profile(
        uid,
        UserProfile(
            name="Saurabh",
            goal="lose 8kg",
            age=34,
            sex="male",
            preferred_workout_modes=["gym", "walking"],
            food_preference="vegetarian",
            sessions_per_week=5,
            constraints=[],
            constraints_asked=True,
            onboarding_complete=True,
            awaiting_onboarding_confirm=False,
        ),
    )

    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    rng = random.Random(42)
    weight = 86.0
    travel_week_idx = max(3, history_weeks // 3)
    bad_week_idx = max(1, history_weeks // 6)

    for w in range(history_weeks, 0, -1):
        week_start = this_monday - timedelta(days=7 * w)
        kind = "steady"
        if w == travel_week_idx:
            kind = "travel"
        elif w == bad_week_idx:
            kind = "bad"

        days_meta: list[tuple[str, str, str]] = []
        if kind == "travel":
            plan_days = [
                WorkoutDay(day="Mon", focus="Hotel full body 20m", duration_min=20, status="done"),
                WorkoutDay(day="Wed", focus="Hotel push + core 20m", duration_min=20, status="done"),
                WorkoutDay(day="Fri", focus="Hotel legs 20m", duration_min=20, status="done"),
            ]
            for i, d in enumerate(plan_days):
                log_workout(uid, (week_start + timedelta(days=i * 2)).isoformat(), d.focus, "done")
                days_meta.append((d.day, d.focus, "done"))
        elif kind == "bad":
            # Stress week: keep the 5-day template but most sessions skipped.
            statuses = ["done", "skipped", "skipped", "skipped", "done"]
            plan_days = []
            for i, ((day, focus, duration), st) in enumerate(
                zip(VETERAN_WEEK_DAYS, statuses, strict=True)
            ):
                plan_days.append(
                    WorkoutDay(
                        day=day,
                        focus=focus,
                        duration_min=duration,
                        status="done" if st == "done" else "planned",
                    )
                )
                log_workout(uid, (week_start + timedelta(days=i)).isoformat(), focus, st)
                days_meta.append((day, focus, st))
        else:
            plan_days = []
            for i, (day, focus, duration) in enumerate(VETERAN_WEEK_DAYS):
                st = "done" if rng.random() < 0.75 else "skipped"
                plan_days.append(
                    WorkoutDay(day=day, focus=focus, duration_min=duration, status="planned")
                )
                log_workout(uid, (week_start + timedelta(days=i)).isoformat(), focus, st)
                days_meta.append((day, focus, st))

        plan = WeekPlan(
            week_start=week_start.isoformat(),
            days=plan_days,
            calorie_target=2100,
            protein_target_g=140,
            notes=(
                "hotel travel week"
                if kind == "travel"
                else ("high work stress" if kind == "bad" else "steady training week")
            ),
        )
        save_week_plan(uid, plan)

        done = sum(1 for _, _, s in days_meta if s == "done")
        skipped = sum(1 for _, _, s in days_meta if s == "skipped")
        summary = _template_memory(
            week_start, kind=kind, planned=len(days_meta), done=done, skipped=skipped
        )
        # --no-llm always uses templates (deterministic demo). LLM path can extend later.
        _ = no_llm
        upsert_weekly_memory(summary, uid)

        # Gentle weight trend with noise
        weight -= 0.2 + rng.uniform(-0.15, 0.05)
        log_weight(uid, (week_start + timedelta(days=6)).isoformat(), round(weight, 1))

    # Current week plan — 5 days: Upper A / Lower A / Conditioning / Upper B / Lower B
    save_week_plan(
        uid,
        WeekPlan(
            week_start=this_monday.isoformat(),
            days=[
                WorkoutDay(day=day, focus=focus, duration_min=duration, status="planned")
                for day, focus, duration in VETERAN_WEEK_DAYS
            ],
            calorie_target=2100,
            protein_target_g=140,
            notes=(
                "Current training week for demo-veteran: "
                "Mon Upper A, Tue Lower A, Wed Conditioning, Thu Upper B, Fri Lower B."
            ),
        ),
    )
    print(
        f"Seeded VETERAN profile {uid} with {history_weeks} history weeks "
        f"(travel=w-{travel_week_idx}, bad=w-{bad_week_idx})"
    )
    print("Seeding personal eval uploads for rag_personal…")
    _seed_personal_docs(uid)
    return uid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["fresh", "veteran"], required=True)
    parser.add_argument("--history-weeks", type=int, default=12)
    parser.add_argument("--no-llm", action="store_true", help="Template memories only")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required to write when DATABASE_URL host is not localhost",
    )
    args = parser.parse_args()
    _require_yes_for_remote(args.yes)

    import subprocess

    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "init_db.py")],
        check=False,
    )

    if args.profile == "fresh":
        seed_fresh()
    else:
        seed_veteran(history_weeks=args.history_weeks, no_llm=args.no_llm)


if __name__ == "__main__":
    main()

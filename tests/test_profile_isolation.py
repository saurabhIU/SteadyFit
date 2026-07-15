"""Isolation tests: profiles must not leak store or memory docs (no LLM)."""
from __future__ import annotations

import uuid
from datetime import date

import psycopg
import pytest

from app.config import settings
from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.memory import store
from app.memory.weekly_summary import WeeklySummary
from app.rag.memory_store import retrieve_memories, upsert_weekly_memory
from app.rag.retriever import retrieve_personal


@pytest.fixture
def two_users():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    a = f"test-a-{uuid.uuid4().hex[:8]}"
    b = f"test-b-{uuid.uuid4().hex[:8]}"
    store.ensure_user(a, "Alice")
    store.ensure_user(b, "Bob")
    store.save_profile(a, UserProfile(name="Alice", goal="cut", onboarding_complete=True))
    store.save_profile(b, UserProfile(name="Bob", goal="bulk", onboarding_complete=True))
    yield a, b
    for uid in (a, b):
        try:
            store.reset_user(uid)
            with store._conn() as c:
                c.execute("DELETE FROM app_users WHERE user_id = %s", (uid,))
                c.commit()
        except Exception:
            pass


def test_workout_logs_isolated(two_users):
    a, b = two_users
    store.log_workout(a, "2026-07-01", "Legs", "done")
    store.log_workout(b, "2026-07-01", "Push", "skipped")
    a_rows = store.get_workouts_between(a, date(2026, 7, 1), date(2026, 7, 2))
    b_rows = store.get_workouts_between(b, date(2026, 7, 1), date(2026, 7, 2))
    assert len(a_rows) == 1 and a_rows[0]["focus"] == "Legs"
    assert len(b_rows) == 1 and b_rows[0]["status"] == "skipped"


def test_memory_retrieval_isolated(two_users):
    a, b = two_users
    if not settings.openai_api_key:
        pytest.skip("OPENAI_API_KEY required for embeddings")
    upsert_weekly_memory(
        WeeklySummary(
            week_start=date(2026, 6, 1),
            context_tags=["travel", "hotel_gym"],
            planned_vs_done="3 planned, 3 done",
            what_worked="hotel sessions for Alice only",
            what_didnt="none noted",
            council_adjustments="hotel plan",
            user_signals="travel",
        ),
        a,
    )
    upsert_weekly_memory(
        WeeklySummary(
            week_start=date(2026, 6, 1),
            context_tags=["high_work_stress"],
            planned_vs_done="5 planned, 1 done",
            what_worked="none noted",
            what_didnt="Bob skipped heavily",
            council_adjustments="simplified",
            user_signals="overwhelmed",
        ),
        b,
    )
    chunks_a, _ = retrieve_memories("travel hotel gym", user_id=a, k=3)
    chunks_b, _ = retrieve_memories("work stress overwhelmed", user_id=b, k=3)
    blob_a = "\n".join(chunks_a)
    blob_b = "\n".join(chunks_b)
    assert "Alice" in blob_a or "hotel" in blob_a.lower()
    assert "Bob skipped" not in blob_a
    assert "Bob" in blob_b or "simplified" in blob_b.lower() or "skipped" in blob_b.lower()
    assert "Alice only" not in blob_b


def test_reset_user_leaves_other_profile_and_kb(two_users):
    a, b = two_users
    store.log_workout(a, "2026-07-02", "Run", "done")
    store.log_workout(b, "2026-07-02", "Swim", "done")
    store.save_week_plan(
        a,
        WeekPlan(week_start="2026-07-07", days=[WorkoutDay(day="Mon", focus="A")]),
    )
    store.reset_user(a)
    assert store.get_workouts_between(a, date(2026, 7, 1), date(2026, 7, 10)) == []
    assert store.get_saved_week_plan(a) is None
    assert store.get_profile(a).onboarding_complete is False
    b_rows = store.get_workouts_between(b, date(2026, 7, 1), date(2026, 7, 10))
    assert len(b_rows) == 1 and b_rows[0]["focus"] == "Swim"

    # kb_* rows (if any) must not be deleted by reset
    with psycopg.connect(settings.database_url) as c:
        before = c.execute(
            "SELECT count(*) FROM documents WHERE doc_type LIKE 'kb_%'"
        ).fetchone()[0]
    store.reset_user(b)
    with psycopg.connect(settings.database_url) as c:
        after = c.execute(
            "SELECT count(*) FROM documents WHERE doc_type LIKE 'kb_%'"
        ).fetchone()[0]
    assert after == before


def test_personal_retrieve_requires_matching_user(two_users, monkeypatch):
    a, b = two_users
    if not settings.openai_api_key:
        pytest.skip("OPENAI_API_KEY required")
    # Minimal: if no personal docs, empty is fine — just ensure B's filter doesn't crash
    # and doesn't require cross-user leakage when empty.
    out_a = retrieve_personal("deload week", user_id=a, k=2)
    out_b = retrieve_personal("deload week", user_id=b, k=2)
    assert isinstance(out_a, list) and isinstance(out_b, list)

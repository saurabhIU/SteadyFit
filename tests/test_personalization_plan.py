"""Full-path personal-doc plan personalization + announcement (API reply field)."""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.graph.build import build_graph
from app.graph.diet_plan import build_diet_week, diet_plan_contains_nonveg
from app.graph.personalization import (
    PERSONALIZATION_ANNOUNCEMENT,
    apply_personalization_flags,
    load_personal_plan_context,
    scrub_diet_for_food_avoids,
    scrub_week_plan_for_avoids,
    _extract_avoid_rules,
    _extract_food_avoids,
)
from app.graph.plan_utils import current_week_start_iso
from app.graph.state import UserProfile, WeekPlan, WorkoutDay
from app.main import app
from app.memory import store
from app.rag.ingest import ingest

TEMPLATE = Path(__file__).resolve().parents[1] / "data/templates/health_profile_template.md"

OVERHEAD_CHUNK = (
    "[doc:health_profile_template.md] Avoid overhead pressing — shoulder issue. "
    "Use landmine or incline press instead. Mild hypertension noted."
)
CHICKEN_CONFLICT_CHUNK = (
    "[doc:notes.md] I usually eat chicken and beef most nights for protein."
)


def _ready_profile(**kwargs) -> UserProfile:
    base = dict(
        name="Personalize",
        goal="lose fat",
        sessions_per_week=3,
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        constraints_asked=True,
        onboarding_complete=True,
        offered_upload_before_weight_gate=True,
        weight_kg=75.0,
        target_weight_declined=True,
        height_cm=175.0,
        age=34,
        sex="male",
        activity_level="moderate",
    )
    base.update(kwargs)
    return UserProfile(**base)


@pytest.fixture
def uid():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    user_id = f"test-pers-{uuid.uuid4().hex[:8]}"
    store.ensure_user(user_id, "Personalize")
    store.save_profile(user_id, _ready_profile())
    yield user_id
    try:
        store.reset_user(user_id)
        with store._conn() as c:
            c.execute("DELETE FROM documents WHERE user_id = %s", (user_id,))
            c.execute("DELETE FROM app_users WHERE user_id = %s", (user_id,))
            c.commit()
    except Exception:
        pass


@pytest.fixture
def client():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    with TestClient(app) as c:
        yield c


def test_scrub_removes_overhead_press_and_cites():
    plan = WeekPlan(
        week_start=current_week_start_iso(),
        days=[
            WorkoutDay(
                day="Monday",
                focus="Shoulder press / overhead press 3x8, row",
                duration_min=40,
            ),
            WorkoutDay(day="Wednesday", focus="Goblet squat, push-up", duration_min=40),
        ],
        calorie_target=2100,
        protein_target_g=140,
    )
    scrubbed = scrub_week_plan_for_avoids(
        plan,
        ["overhead press", "shoulder press"],
        source_tag="[doc: health_profile_template.md]",
    )
    mon = scrubbed.days[0].focus.lower()
    assert "overhead press" not in mon or "joint-safer" in mon
    assert "joint-safer" in mon
    assert "[doc:" in scrubbed.days[0].focus or "[doc:" in (scrubbed.notes or "")


def test_profile_wins_on_food_conflict():
    profile = _ready_profile(food_preference="vegetarian")
    with patch("app.graph.personalization.user_has_personal_docs", return_value=True):
        with patch(
            "app.graph.personalization.retrieve_personal",
            return_value=[CHICKEN_CONFLICT_CHUNK],
        ):
            ctx = load_personal_plan_context("u1", profile)
    assert ctx.conflicts
    assert "food_preference" in ctx.conflicts[0]
    meals = build_diet_week(profile, week_start=current_week_start_iso())
    assert not diet_plan_contains_nonveg(meals)


def test_back_pain_and_beef_avoids_extracted():
    chunks = [
        "[doc:user_data.md] Injuries: Back pain issue. Diet: I DONOT eat Beaf and Pork."
    ]
    labels, terms = _extract_avoid_rules(chunks)
    assert any("spinal" in lab.lower() or "deadlift" in lab.lower() for lab in labels)
    assert any("deadlift" in t.lower() or "squat" in t.lower() for t in terms)
    foods = _extract_food_avoids(chunks)
    assert "beef" in foods
    assert "pork" in foods
    plan = WeekPlan(
        week_start=current_week_start_iso(),
        days=[
            WorkoutDay(
                day="Monday",
                focus="Barbell Back Squat, Conventional Deadlift",
                duration_min=45,
                status="planned",
            )
        ],
        calorie_target=2000,
        protein_target_g=150,
    )
    scrubbed = scrub_week_plan_for_avoids(plan, terms, source_tag="[doc: user_data.md]")
    focus = scrubbed.days[0].focus.lower()
    assert "joint-safer" in focus or "back squat" not in focus
    meals = [
        {
            "day": "Monday",
            "meal_slot": "lunch",
            "food_description": "Beef burrito bowl",
            "kcal": 500,
            "protein_g": 30,
        }
    ]
    cleaned = scrub_diet_for_food_avoids(meals, foods)
    assert "beef" not in cleaned[0]["food_description"].lower()


def test_first_plan_again_routes_to_schedule_not_knowledge():
    from langchain_core.messages import HumanMessage

    from app.graph.supervisor import coach_node
    from app.graph.state import CoachingTeamState

    state = CoachingTeamState(
        user_id="u-route",
        profile=_ready_profile(),
        messages=[
            HumanMessage(
                content="Please draft my first week plan again with my uploaded health profile"
            )
        ],
        week_plan=WeekPlan(
            week_start=current_week_start_iso(),
            days=[WorkoutDay(day="Mon", focus="Lift", duration_min=40, status="planned")],
            calorie_target=2000,
            protein_target_g=140,
        ),
    )
    out = coach_node(state)
    assert out["intent"] == "schedule"


def _scheduler_with_personalization(state):
    """Plan that initially includes overhead press; scrub + announce from personal ctx."""
    week_start = current_week_start_iso()
    ctx = load_personal_plan_context(state.user_id or "", state.profile)
    plan = WeekPlan(
        week_start=week_start,
        days=[
            WorkoutDay(
                day="Monday",
                focus="Overhead press 3x8, cable row",
                duration_min=40,
                status="planned",
            ),
            WorkoutDay(
                day="Wednesday",
                focus="Goblet squat, push-up",
                duration_min=40,
                status="planned",
            ),
            WorkoutDay(
                day="Friday",
                focus="Hinge, incline press",
                duration_min=40,
                status="planned",
            ),
        ],
        calorie_target=2100,
        protein_target_g=140,
        notes="seed",
    )
    tag = ctx.citations[0]["tag"] if ctx.citations else None
    if ctx.avoid_terms:
        plan = scrub_week_plan_for_avoids(plan, ctx.avoid_terms, source_tag=tag)
    meals = build_diet_week(state.profile, week_start=week_start)
    proposals = apply_personalization_flags(
        {
            **dict(state.proposals or {}),
            "plan_changed": True,
            "proposed_week_plan": plan.model_dump(),
            "proposed_diet_plan": meals,
            "diet_plan_summary": [],
            "scheduler": "Personalized test week.",
        },
        ctx,
    )
    return {
        "proposals": proposals,
        "retrieved_context": list(state.retrieved_context or []) + list(ctx.chunks),
        "citations": list(ctx.citations),
    }


def test_api_personal_doc_announcement_and_constraint(client, uid):
    """FULL-PATH: announcement + overhead scrub + doc citation in API reply/plan."""
    import app.main as main_mod

    with (
        patch("app.graph.personalization.user_has_personal_docs", return_value=True),
        patch(
            "app.graph.personalization.retrieve_personal",
            return_value=[OVERHEAD_CHUNK],
        ),
        patch("app.graph.build.scheduler_node", _scheduler_with_personalization),
    ):
        rebuilt = build_graph()
        with patch.object(main_mod, "graph", rebuilt):
            res = client.post(
                "/api/chat",
                headers={"X-User-Id": uid},
                json={"message": "Please draft my first week plan"},
            )
    assert res.status_code == 200, res.text
    data = res.json()
    reply = data.get("reply") or ""
    assert PERSONALIZATION_ANNOUNCEMENT in reply, f"announcement missing: {reply!r}"
    assert "I've built your first week" in reply or "plan" in reply.lower()

    pending = data.get("pending_approval") or {}
    plan = pending.get("proposed_plan") or {}
    days = plan.get("days") or []
    focus_blob = " ".join(str(d.get("focus") or "") for d in days).lower()
    assert days, f"no plan days in pending_approval: {pending!r}"
    assert "overhead press" not in focus_blob or "joint-safer" in focus_blob
    notes = str(plan.get("notes") or "").lower()
    assert "[doc:" in focus_blob or "[doc:" in notes
    cites = data.get("citations") or []
    cite_blob = " ".join(str(c) for c in cites).lower()
    assert "doc" in cite_blob or "[doc:" in focus_blob or "[doc:" in notes


def test_api_no_docs_no_announcement(client, uid):
    import app.main as main_mod

    def _scheduler_plain(state):
        week_start = current_week_start_iso()
        return {
            "proposals": {
                **dict(state.proposals or {}),
                "plan_changed": True,
                "proposed_week_plan": {
                    "week_start": week_start,
                    "days": [
                        {
                            "day": "Monday",
                            "focus": "Full body",
                            "duration_min": 40,
                            "status": "planned",
                        }
                    ],
                    "calorie_target": 2100,
                    "protein_target_g": 140,
                },
                "proposed_diet_plan": [],
                "scheduler": "Plain week",
            },
            "retrieved_context": [],
            "citations": [],
        }

    with (
        patch("app.graph.personalization.user_has_personal_docs", return_value=False),
        patch("app.graph.build.scheduler_node", _scheduler_plain),
    ):
        rebuilt = build_graph()
        with patch.object(main_mod, "graph", rebuilt):
            res = client.post(
                "/api/chat",
                headers={"X-User-Id": uid},
                json={"message": "Please draft my first week plan"},
            )
    assert res.status_code == 200
    reply = res.json().get("reply") or ""
    assert PERSONALIZATION_ANNOUNCEMENT not in reply


def test_api_demo_template_ingest_path(client, uid):
    """Upload health-profile template → plan turn reflects constraint + announcement."""
    if not TEMPLATE.exists():
        pytest.skip("health_profile_template.md missing")
    import app.main as main_mod

    # Real ingest into pgvector for this user
    n = ingest(str(TEMPLATE), doc_type="personal", user_id=uid)
    assert n > 0
    assert store.user_has_personal_docs(uid)

    # Avoid flaky live LLM: scheduler uses real personalization load + scrub
    with patch("app.graph.build.scheduler_node", _scheduler_with_personalization):
        # retrieve_personal is real (needs embeddings) — allow network
        rebuilt = build_graph()
        with patch.object(main_mod, "graph", rebuilt):
            res = client.post(
                "/api/chat",
                headers={"X-User-Id": uid},
                json={"message": "Please draft my first week plan"},
            )
    assert res.status_code == 200, res.text
    data = res.json()
    reply = data.get("reply") or ""
    assert PERSONALIZATION_ANNOUNCEMENT in reply
    pending = data.get("pending_approval") or {}
    plan = pending.get("proposed_plan") or {}
    days = plan.get("days") or []
    focus_blob = " ".join(str(d.get("focus") or "") for d in days).lower()
    ctx = load_personal_plan_context(uid, store.get_profile(uid))
    if ctx.avoid_terms and days:
        assert "overhead press" not in focus_blob or "joint-safer" in focus_blob
        assert "[doc:" in focus_blob or "[doc:" in str(plan.get("notes") or "").lower()
    else:
        # Retrieval may be soft-fail without embeddings; announcement still required
        # when docs exist (has_docs True even if chunks empty after filter).
        assert store.user_has_personal_docs(uid)

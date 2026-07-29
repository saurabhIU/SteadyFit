"""Full-path eval: plan_changed replies keep flagged additive content in API reply."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage

from app.config import settings
from app.graph.build import build_graph
from app.graph.plan_utils import current_week_start_iso
from app.graph.state import CoachingTeamState, UserProfile
from app.graph.supervisor import (
    _compose_plan_changed_reply,
    _flagged_reply_additions,
    coaching_team_node,
)
from app.main import app
from app.memory import store

MARKER = "MARKER_PENDING_ADDITIVE_CONTENT_XYZ"


def test_flagged_additions_collected():
    assert _flagged_reply_additions({
        "personalization_note": "Note A",
        "reply_additions": ["Note B", ""],
        "offer_upload": True,
        "upload_offer_text": "Note C",
    }) == ["Note B", "Note A", "Note C"]


def test_compose_appends_to_intro():
    state = CoachingTeamState(
        profile=UserProfile(name="A", goal="lose fat", preferred_workout_modes=["gym"]),
        proposals={
            "plan_changed": True,
            "personalization_note": MARKER,
        },
    )
    out = _compose_plan_changed_reply(state, "I've built your first week. Take a look below.")
    assert "I've built your first week" in out
    assert MARKER in out
    # Announcement/note is placed first so it stays visible above the plan card.
    assert out.index(MARKER) < out.index("I've built")


def test_coaching_team_node_preserves_personalization_note():
    state = CoachingTeamState(
        user_id="u-additive",
        profile=UserProfile(
            name="A",
            goal="lose fat",
            preferred_workout_modes=["gym"],
            onboarding_complete=True,
        ),
        messages=[HumanMessage(content="Build my week")],
        proposals={
            "plan_changed": True,
            "proposed_week_plan": {
                "week_start": current_week_start_iso(),
                "days": [
                    {"day": "Monday", "focus": "Full body", "duration_min": 40, "status": "planned"}
                ],
                "calorie_target": 2000,
                "protein_target_g": 140,
            },
            "personalization_note": MARKER,
            "scheduler": "draft",
        },
    )
    out = coaching_team_node(state)
    reply = out["messages"][0]["content"]
    assert MARKER in reply
    assert "take a look" in reply.lower() or "look below" in reply.lower()


@pytest.fixture
def uid():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    user_id = f"test-additive-{uuid.uuid4().hex[:8]}"
    store.ensure_user(user_id, "Additive")
    store.save_profile(
        user_id,
        UserProfile(
            name="Additive",
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
        ),
    )
    yield user_id
    try:
        store.reset_user(user_id)
        with store._conn() as c:
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


def _fake_scheduler_with_marker(state):
    """Deterministic plan_changed turn that flags additive content."""
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
                        "focus": "Full body — goblet squat, row",
                        "duration_min": 40,
                        "status": "planned",
                    },
                    {
                        "day": "Wednesday",
                        "focus": "Full body — hinge, push-up",
                        "duration_min": 40,
                        "status": "planned",
                    },
                    {
                        "day": "Friday",
                        "focus": "Full body — press alternative, pull",
                        "duration_min": 40,
                        "status": "planned",
                    },
                ],
                "calorie_target": 2100,
                "protein_target_g": 140,
                "notes": "test plan",
            },
            "proposed_diet_plan": [],
            "diet_plan_summary": [],
            "scheduler": "Structured test week ready.",
            "personalization_note": MARKER,
        },
        "retrieved_context": list(state.retrieved_context or []),
        "citations": list(state.citations or []),
    }


def test_coaching_team_failsafe_adds_announcement_when_docs_exist():
    """Even if scheduler forgot personalization_note, council must append it."""
    from app.graph.personalization import PERSONALIZATION_ANNOUNCEMENT
    from app.graph.supervisor import coaching_team_node

    state = CoachingTeamState(
        user_id="u-docs",
        profile=UserProfile(
            name="A",
            goal="lose fat",
            preferred_workout_modes=["gym"],
            onboarding_complete=True,
        ),
        messages=[HumanMessage(content="Build my week")],
        proposals={
            "plan_changed": True,
            "proposed_week_plan": {
                "week_start": current_week_start_iso(),
                "days": [
                    {
                        "day": "Monday",
                        "focus": "Overhead press 3x8, row",
                        "duration_min": 40,
                        "status": "planned",
                    }
                ],
                "calorie_target": 2000,
                "protein_target_g": 140,
            },
            "scheduler": "draft",
            # Intentionally NO personalization_note
        },
    )
    with (
        patch("app.graph.personalization.user_has_personal_docs", return_value=True),
        patch(
            "app.graph.personalization.retrieve_personal",
            return_value=[
                "[doc:health.md] Avoid overhead pressing — shoulder issue."
            ],
        ),
    ):
        out = coaching_team_node(state)
    reply = out["messages"][0]["content"]
    assert PERSONALIZATION_ANNOUNCEMENT in reply
    plan = out["proposals"].get("proposed_week_plan") or {}
    focus = " ".join(d.get("focus", "") for d in plan.get("days") or []).lower()
    assert "overhead press" not in focus or "joint-safer" in focus


def test_api_plan_changed_reply_includes_flagged_addition(client, uid):
    """FULL-PATH: flagged content must appear in /api/chat reply, not only history."""
    import app.main as main_mod

    with patch("app.graph.build.scheduler_node", _fake_scheduler_with_marker):
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
    assert MARKER in reply, f"additive content missing from API reply: {reply!r}"
    assert data.get("pending_approval") is not None
    assert "week" in reply.lower() or "plan" in reply.lower()

"""Pre-weight-gate upload offer — unit + full-path /api/chat evals."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage

from app.config import settings
from app.graph.agents.intake import _handoff_first_plan, intake_node
from app.graph.build import route_from_intake
from app.graph.state import CoachingTeamState, UserProfile
from app.graph.upload_offer import (
    JUST_ASK_CHIP,
    UPLOAD_BEFORE_WEIGHT_QUESTION,
    UPLOAD_NOW_CHIP,
    UPLOAD_NOW_INSTRUCT,
    maybe_upload_offer_or_weight,
)
from app.graph.weight_gate import WEIGHT_QUESTION
from app.main import app
from app.memory import store


def _gate_ready_profile(**kwargs) -> UserProfile:
    """Onboarding confirmed; about to enter diet metrics / upload offer."""
    base = dict(
        name="Offer Tester",
        goal="lose fat",
        sessions_per_week=3,
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        constraints_asked=True,
        onboarding_complete=True,
        awaiting_onboarding_confirm=False,
        weight_kg=None,
        weight_declined=False,
        offered_upload_before_weight_gate=False,
        awaiting_upload_before_weight=False,
        shown_upload_hint=False,
    )
    base.update(kwargs)
    return UserProfile(**base)


def _confirm_profile(**kwargs) -> UserProfile:
    p = _gate_ready_profile(
        onboarding_complete=False,
        awaiting_onboarding_confirm=True,
        **kwargs,
    )
    return p


@pytest.fixture
def uid():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    with store._conn() as c:
        c.execute(
            """
            ALTER TABLE user_profiles
              ADD COLUMN IF NOT EXISTS offered_upload_before_weight_gate
                BOOLEAN NOT NULL DEFAULT FALSE
            """
        )
        c.execute(
            """
            ALTER TABLE user_profiles
              ADD COLUMN IF NOT EXISTS awaiting_upload_before_weight
                BOOLEAN NOT NULL DEFAULT FALSE
            """
        )
        c.commit()
    user_id = f"test-upload-offer-{uuid.uuid4().hex[:8]}"
    store.ensure_user(user_id, "Upload Offer")
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


def test_handoff_no_longer_appends_post_plan_hint():
    profile = _gate_ready_profile(
        weight_kg=75,
        height_cm=175,
        age=34,
        sex="male",
        activity_level="moderate",
        target_weight_declined=True,
    )
    state = CoachingTeamState(user_id="hint-retired", profile=profile)
    with patch("app.graph.agents.intake.save_profile"):
        out = _handoff_first_plan(profile, state, preamble="Drafting your first week.")
    assert "Update tab" not in out["messages"][0]["content"]
    assert "Totally optional" not in out["messages"][0]["content"]
    assert out["proposals"].get("offer_upload") is None


def test_maybe_offer_when_no_docs():
    profile = _gate_ready_profile()
    with patch("app.graph.upload_offer.user_has_personal_docs", return_value=False):
        out = maybe_upload_offer_or_weight(profile, "u1")
    assert UPLOAD_BEFORE_WEIGHT_QUESTION in out["messages"][0]["content"]
    assert out["quick_replies"] == [UPLOAD_NOW_CHIP, JUST_ASK_CHIP]
    assert out["profile"].awaiting_upload_before_weight is True
    assert out["proposals"].get("plan_changed") is False
    assert route_from_intake(
        CoachingTeamState(intent=out["intent"], proposals=out["proposals"])
    ) == "end"


def test_maybe_offer_skipped_when_docs_exist():
    profile = _gate_ready_profile()
    with patch("app.graph.upload_offer.user_has_personal_docs", return_value=True):
        out = maybe_upload_offer_or_weight(profile, "u1")
    assert WEIGHT_QUESTION in out["messages"][0]["content"]
    assert out["profile"].offered_upload_before_weight_gate is True
    assert UPLOAD_NOW_CHIP not in out["quick_replies"]


def test_confirm_shows_offer_not_weight(uid):
    profile = _confirm_profile()
    store.save_profile(uid, profile)
    state = CoachingTeamState(
        user_id=uid,
        profile=profile,
        messages=[HumanMessage(content="Yes, looks good")],
    )
    with patch("app.graph.upload_offer.user_has_personal_docs", return_value=False):
        out = intake_node(state)
    assert out["intent"] == "intake"
    assert UPLOAD_BEFORE_WEIGHT_QUESTION in out["messages"][0]["content"]
    assert UPLOAD_NOW_CHIP in out["quick_replies"]
    assert JUST_ASK_CHIP in out["quick_replies"]
    assert route_from_intake(
        CoachingTeamState(intent=out["intent"], proposals=out["proposals"])
    ) == "end"
    saved = store.get_profile(uid)
    assert saved.awaiting_upload_before_weight is True
    assert saved.offered_upload_before_weight_gate is False


def test_just_ask_proceeds_to_weight(uid):
    profile = _gate_ready_profile(awaiting_upload_before_weight=True)
    store.save_profile(uid, profile)
    state = CoachingTeamState(
        user_id=uid,
        profile=profile,
        messages=[HumanMessage(content=JUST_ASK_CHIP)],
        proposals={"ask_upload_before_weight": True},
    )
    out = intake_node(state)
    assert WEIGHT_QUESTION in out["messages"][0]["content"]
    assert UPLOAD_BEFORE_WEIGHT_QUESTION not in out["messages"][0]["content"]
    saved = store.get_profile(uid)
    assert saved.offered_upload_before_weight_gate is True
    assert saved.awaiting_upload_before_weight is False
    assert saved.awaiting_weight_for_first_plan is True


def test_upload_now_instructs_and_sets_flag(uid):
    profile = _gate_ready_profile(awaiting_upload_before_weight=True)
    store.save_profile(uid, profile)
    state = CoachingTeamState(
        user_id=uid,
        profile=profile,
        messages=[HumanMessage(content=UPLOAD_NOW_CHIP)],
        proposals={"ask_upload_before_weight": True},
    )
    out = intake_node(state)
    assert UPLOAD_NOW_INSTRUCT in out["messages"][0]["content"]
    assert out["intent"] == "intake"
    assert route_from_intake(
        CoachingTeamState(intent=out["intent"], proposals=out["proposals"])
    ) == "end"
    saved = store.get_profile(uid)
    assert saved.offered_upload_before_weight_gate is True
    assert saved.awaiting_upload_before_weight is False
    assert saved.awaiting_weight_for_first_plan is True


def test_ambiguous_free_text_reoffers_without_extracting(uid):
    profile = _gate_ready_profile(awaiting_upload_before_weight=True, goal="lose fat")
    store.save_profile(uid, profile)
    state = CoachingTeamState(
        user_id=uid,
        profile=profile,
        messages=[HumanMessage(content="What's a good creatine dose?")],
        proposals={"ask_upload_before_weight": True},
    )
    with patch("app.graph.agents.intake._brief_aside", return_value="Quick note on that."):
        out = intake_node(state)
    text = out["messages"][0]["content"]
    assert UPLOAD_BEFORE_WEIGHT_QUESTION in text
    assert UPLOAD_NOW_CHIP in out["quick_replies"]
    saved = store.get_profile(uid)
    assert saved.offered_upload_before_weight_gate is False
    assert saved.awaiting_upload_before_weight is True
    assert saved.goal == "lose fat"


def _seed_confirm_ready(user_id: str) -> None:
    store.save_profile(user_id, _confirm_profile(name="API Guest"))


def test_api_offer_survives_final_reply(client, uid):
    """Full-path: confirm → API reply field contains offer (intake→END, not council)."""
    _seed_confirm_ready(uid)
    with patch("app.graph.upload_offer.user_has_personal_docs", return_value=False):
        res = client.post(
            "/api/chat",
            headers={"X-User-Id": uid},
            json={"message": "Yes, looks good"},
        )
    assert res.status_code == 200, res.text
    data = res.json()
    assert UPLOAD_BEFORE_WEIGHT_QUESTION in (data.get("reply") or "")
    assert UPLOAD_NOW_CHIP in (data.get("quick_replies") or [])
    assert JUST_ASK_CHIP in (data.get("quick_replies") or [])
    assert data.get("pending_approval") is None
    saved = store.get_profile(uid)
    assert saved.awaiting_upload_before_weight is True


def test_api_just_ask_then_weight(client, uid):
    _seed_confirm_ready(uid)
    with patch("app.graph.upload_offer.user_has_personal_docs", return_value=False):
        r1 = client.post(
            "/api/chat",
            headers={"X-User-Id": uid},
            json={"message": "Yes, looks good"},
        )
    assert r1.status_code == 200
    thread = r1.json()["thread_id"]
    r2 = client.post(
        "/api/chat",
        headers={"X-User-Id": uid},
        json={"message": JUST_ASK_CHIP, "thread_id": thread},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert WEIGHT_QUESTION in (data.get("reply") or "")
    assert UPLOAD_BEFORE_WEIGHT_QUESTION not in (data.get("reply") or "")
    assert UPLOAD_NOW_CHIP not in (data.get("quick_replies") or [])
    # Choice never reappears
    r3 = client.post(
        "/api/chat",
        headers={"X-User-Id": uid},
        json={"message": "Prefer not to say", "thread_id": thread},
    )
    assert r3.status_code == 200
    assert UPLOAD_BEFORE_WEIGHT_QUESTION not in (r3.json().get("reply") or "")
    assert store.get_profile(uid).offered_upload_before_weight_gate is True


def test_api_upload_now_instruct(client, uid):
    _seed_confirm_ready(uid)
    with patch("app.graph.upload_offer.user_has_personal_docs", return_value=False):
        r1 = client.post(
            "/api/chat",
            headers={"X-User-Id": uid},
            json={"message": "Yes, looks good"},
        )
    thread = r1.json()["thread_id"]
    r2 = client.post(
        "/api/chat",
        headers={"X-User-Id": uid},
        json={"message": UPLOAD_NOW_CHIP, "thread_id": thread},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert UPLOAD_NOW_INSTRUCT in (data.get("reply") or "")
    assert data.get("pending_approval") is None
    assert store.get_profile(uid).offered_upload_before_weight_gate is True
    # Next message resumes weight gate (no re-offer)
    r3 = client.post(
        "/api/chat",
        headers={"X-User-Id": uid},
        json={"message": "ready", "thread_id": thread},
    )
    assert r3.status_code == 200
    assert WEIGHT_QUESTION in (r3.json().get("reply") or "")
    assert UPLOAD_BEFORE_WEIGHT_QUESTION not in (r3.json().get("reply") or "")


def test_api_skips_offer_when_personal_docs(client, uid):
    _seed_confirm_ready(uid)
    with patch("app.graph.upload_offer.user_has_personal_docs", return_value=True):
        res = client.post(
            "/api/chat",
            headers={"X-User-Id": uid},
            json={"message": "Yes, looks good"},
        )
    assert res.status_code == 200
    data = res.json()
    assert WEIGHT_QUESTION in (data.get("reply") or "")
    assert UPLOAD_BEFORE_WEIGHT_QUESTION not in (data.get("reply") or "")
    assert store.get_profile(uid).offered_upload_before_weight_gate is True

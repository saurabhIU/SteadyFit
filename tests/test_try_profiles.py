"""Ephemeral try-profile flow: create, cleanup, weekly-review exclusion."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.graph.intake import needs_intake
from app.memory import store


@pytest.fixture
def db_ready():
    if not settings.database_url:
        pytest.skip("DATABASE_URL required")
    # Ensure ephemeral columns exist (idempotent).
    with store._conn() as c:
        c.execute(
            """
            ALTER TABLE user_profiles
              ADD COLUMN IF NOT EXISTS is_ephemeral BOOLEAN NOT NULL DEFAULT false
            """
        )
        c.execute(
            """
            ALTER TABLE user_profiles
              ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ NULL
            """
        )
        c.commit()


@pytest.fixture
def client(db_ready):
    from app.main import app

    with TestClient(app) as c:
        yield c


def _force_expired(user_id: str) -> None:
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    with store._conn() as c:
        c.execute(
            """
            UPDATE user_profiles
            SET is_ephemeral = TRUE, expires_at = %s
            WHERE user_id = %s
            """,
            (past, user_id),
        )
        c.commit()


def test_try_profile_rejects_extra_body_fields(client):
    res = client.post("/api/profiles/try", json={"name": "Nope"})
    assert res.status_code == 422


def test_try_profile_creates_ephemeral_blank(client):
    res = client.post("/api/profiles/try", json={})
    assert res.status_code == 200
    uid = res.json()["user_id"]
    assert uid.startswith("try-")
    assert store.user_exists(uid)
    assert store.is_ephemeral_user(uid)
    profile = store.get_profile(uid)
    assert profile.onboarding_complete is False
    assert needs_intake(profile) is True
    store.delete_user(uid)


def test_try_profile_rate_limit_returns_friendly_429(client):
    """Decorator is wired; handler returns friendly 429 for /api/profiles/try."""
    from app.main import _rate_limit_handler
    from starlette.requests import Request

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/profiles/try",
        "raw_path": b"/api/profiles/try",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    request = Request(scope)
    fake_limit = type(
        "L",
        (),
        {
            "error_message": None,
            "limit": "20 per 1 minute",
            "get_expiry": staticmethod(lambda: None),
        },
    )()
    response = _rate_limit_handler(request, RateLimitExceeded(fake_limit))
    assert response.status_code == 429
    body = response.body.decode()
    assert "try" in body.lower() or "wait" in body.lower()

    # Endpoint still has the same limiter decorator as /api/chat.
    from app.main import api_try_profile, chat

    assert getattr(api_try_profile, "__wrapped__", None) is not None
    assert getattr(chat, "__wrapped__", None) is not None


def test_cleanup_deletes_expired_only(db_ready):
    live = store.create_try_user()
    expired = store.create_try_user()
    stable = f"test-stable-{uuid.uuid4().hex[:6]}"
    store.ensure_user(stable, "Stable")
    _force_expired(expired)

    deleted = store.delete_expired_ephemeral_users()
    assert expired in deleted
    assert live not in deleted
    assert store.user_exists(live)
    assert not store.user_exists(expired)
    assert store.user_exists(stable)
    assert store.is_ephemeral_user(stable) is False

    store.delete_user(live)
    with store._conn() as c:
        c.execute("DELETE FROM app_users WHERE user_id = %s", (stable,))
        c.commit()


def test_weekly_review_excludes_ephemeral(db_ready):
    try_uid = store.create_try_user()
    stable = f"test-wr-{uuid.uuid4().hex[:6]}"
    store.ensure_user(stable, "Weekly")

    review_ids = {u["user_id"] for u in store.list_users_for_weekly_review()}
    assert try_uid not in review_ids
    assert stable in review_ids
    # Full list still includes try guests for admin/debug.
    all_ids = {u["user_id"] for u in store.list_users(include_ephemeral=True)}
    assert try_uid in all_ids

    store.delete_user(try_uid)
    with store._conn() as c:
        c.execute("DELETE FROM app_users WHERE user_id = %s", (stable,))
        c.commit()


def test_try_profile_intake_same_as_demo_new(db_ready):
    """Blank try-* profile triggers the same intake gate as demo-new."""
    from app.graph.state import UserProfile

    try_uid = store.create_try_user()
    try_profile = store.get_profile(try_uid)
    fresh = UserProfile(name="Demo New", goal="", onboarding_complete=False)
    assert needs_intake(try_profile) is True
    assert needs_intake(fresh) is True
    assert try_profile.onboarding_complete is False
    store.delete_user(try_uid)


def test_cleanup_endpoint_requires_secret(client, monkeypatch):
    monkeypatch.setattr(settings, "internal_cron_secret", "test-secret")
    bad = client.post("/internal/cleanup-expired-profiles")
    assert bad.status_code == 401
    ok = client.post(
        "/internal/cleanup-expired-profiles",
        headers={"X-Internal-Secret": "test-secret"},
    )
    assert ok.status_code == 200
    assert ok.json()["ok"] is True

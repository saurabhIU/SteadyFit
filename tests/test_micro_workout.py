"""Tests for the \"I have 10 minutes\" micro-workout helper."""

from app.graph.micro_workout import (
    TEN_MINUTE_CHIP,
    build_ten_minute_reply,
    looks_like_ten_minute_request,
)
from app.graph.state import UserProfile


def test_chip_and_paraphrases_match():
    assert looks_like_ten_minute_request(TEN_MINUTE_CHIP)
    assert looks_like_ten_minute_request("I only have 10 minutes")
    assert looks_like_ten_minute_request("got ten minutes — what can I do?")
    assert looks_like_ten_minute_request("quick 10-min workout please")
    assert not looks_like_ten_minute_request("I have 40 minutes for legs")
    assert not looks_like_ten_minute_request("re-plan my week")


def test_reply_is_concrete_and_short():
    profile = UserProfile(
        name="Saurabh",
        goal="stay consistent",
        preferred_workout_modes=["home"],
        onboarding_complete=True,
    )
    reply = build_ten_minute_reply(profile)
    assert "10 minutes" in reply.lower() or "10 minute" in reply.lower()
    assert "0:00" in reply
    assert "Saurabh" in reply
    assert "plan_changed" not in reply


def test_knee_constraint_avoids_lunges():
    profile = UserProfile(
        name="Sam",
        preferred_workout_modes=["gym"],
        constraints=["left knee sore"],
        onboarding_complete=True,
    )
    reply = build_ten_minute_reply(profile).lower()
    assert "knee" in reply
    assert "lunge" not in reply

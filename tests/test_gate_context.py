"""Unit tests for scope-gate pending bypass and continuation helpers (no live LLM)."""
from types import SimpleNamespace

from app.chat_pipeline import should_skip_scope_gate
from app.graph.state import UserProfile
from app.security import (
    GENTLE_CLARIFICATION_REPLY,
    classify_scope,
    gentle_clarification_reply,
    is_first_user_turn,
    looks_like_fitness_query,
    looks_like_short_affirmation,
    looks_like_short_reject,
    prior_turns_from_messages,
)


def test_short_affirmations_detected():
    for msg in ("yes please", "Yes", "sure", "sounds good", "ok", "prefer not to say"):
        assert looks_like_short_affirmation(msg), msg
    assert not looks_like_short_affirmation("what's a good stock to buy?")
    assert not looks_like_short_affirmation("actually my knee hurts")


def test_short_reject_detected():
    assert looks_like_short_reject("no")
    assert looks_like_short_reject("keep my plan")
    assert not looks_like_short_reject("yes please")


def test_pending_approve_skips_scope_gate():
    profile = UserProfile(name="Saurabh", onboarding_complete=True)
    pending = {"type": "plan_approval", "proposed_plan": {}}
    assert should_skip_scope_gate(profile=profile, pending_approval=pending) is True


def test_intake_incomplete_skips_scope_gate():
    profile = UserProfile(
        name="Demo New",
        goal="lose fat",
        onboarding_complete=False,
        awaiting_onboarding_confirm=False,
    )
    assert should_skip_scope_gate(profile=profile, pending_approval=None) is True


def test_complete_profile_no_pending_does_not_skip():
    profile = UserProfile(
        name="Saurabh",
        goal="lose 8kg",
        sessions_per_week=5,
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        onboarding_complete=True,
    )
    assert should_skip_scope_gate(profile=profile, pending_approval=None) is False


def test_awaiting_confirm_skips_scope_gate():
    profile = UserProfile(
        name="Demo New",
        goal="lose fat",
        sessions_per_week=3,
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        onboarding_complete=False,
        awaiting_onboarding_confirm=True,
    )
    assert should_skip_scope_gate(profile=profile, pending_approval=None) is True


def test_continuation_affirmation_in_scope_without_llm():
    prior = (
        "Want me to help you hit 140g protein/day from vegetarian sources, "
        "or dial in your creatine timing?"
    )
    assert classify_scope("yes please", prior_assistant=prior) == "in_scope"


def test_cold_affirmation_in_scope_maps_to_gentle_template():
    assert classify_scope("yes please", prior_assistant=None) == "in_scope"
    assert gentle_clarification_reply() == GENTLE_CLARIFICATION_REPLY
    assert "plan" in GENTLE_CLARIFICATION_REPLY.lower()


def test_prior_turns_from_messages():
    msgs = [
        {"role": "user", "content": "what supplements should I take"},
        SimpleNamespace(type="ai", content="Want protein plan or creatine timing?"),
        {"role": "user", "content": "yes please"},
    ]
    # Latest user is included; prior assistant is still the coach offer before it
    # when we pass history WITHOUT the latest user:
    prior_a, prior_u = prior_turns_from_messages(msgs[:-1])
    assert prior_a and "protein" in prior_a.lower()
    assert prior_u and "supplements" in prior_u.lower()


def test_empty_history_is_first_user_turn():
    assert is_first_user_turn([]) is True
    assert is_first_user_turn(None) is True  # type: ignore[arg-type]


def test_history_with_turns_is_not_first_user_turn():
    assert is_first_user_turn([{"role": "assistant", "content": "Hi — I'm Steady."}]) is False
    assert is_first_user_turn([{"role": "user", "content": "hello"}]) is False


def test_first_user_turn_skips_scope_gate_for_complete_profile():
    profile = UserProfile(
        name="Saurabh",
        goal="lose 8kg",
        sessions_per_week=5,
        preferred_workout_modes=["gym"],
        food_preference="vegetarian",
        onboarding_complete=True,
    )
    assert should_skip_scope_gate(profile=profile, pending_approval=None, history=[]) is True
    assert (
        should_skip_scope_gate(
            profile=profile,
            pending_approval=None,
            history=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}],
        )
        is False
    )


def test_declarative_goal_statements_are_fitness_scope():
    for msg in (
        "I am looking for fat loss",
        "I want to build muscle",
        "trying to get fit",
        "goal is to lose weight",
        "I'm 34 and vegetarian",
    ):
        assert looks_like_fitness_query(msg), msg
        assert classify_scope(msg, prior_assistant=None) == "in_scope", msg


def test_weather_is_out_of_scope_without_llm():
    assert classify_scope("what's the weather today", prior_assistant=None) == "out_of_scope"

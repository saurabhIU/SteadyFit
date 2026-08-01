"""Adherence check-in → 'yes schedule' continuation routing (no LLM)."""
from langchain_core.messages import AIMessage, HumanMessage

from app.graph.adherence_continue import (
    YES_SCHEDULE_CHIP,
    YES_SCHEDULE_CHIP_LABEL,
    looks_like_yes_schedule_chip,
    prior_was_adherence_schedule_offer,
    reply_asks_clarifying_intake,
)
from app.graph.plan_utils import current_week_start_iso
from app.graph.state import CoachingTeamState, UserProfile, WeekPlan, WorkoutDay
from app.graph.supervisor import coach_node


def _veteran_profile(**kwargs) -> UserProfile:
    data = dict(
        name="John",
        goal="lose 8kg",
        sessions_per_week=5,
        preferred_workout_modes=["gym", "walking"],
        food_preference="vegetarian",
        constraints=["Right knee mild irritation"],
        constraints_asked=True,
        onboarding_complete=True,
    )
    data.update(kwargs)
    return UserProfile(**data)


def _week() -> WeekPlan:
    return WeekPlan(
        week_start=current_week_start_iso(),
        days=[
            WorkoutDay(day="Mon", focus="Upper A", duration_min=50, status="planned"),
            WorkoutDay(day="Wed", focus="Lower A", duration_min=50, status="planned"),
            WorkoutDay(day="Fri", focus="Conditioning", duration_min=35, status="planned"),
        ],
        calorie_target=2100,
        protein_target_g=140,
    )


def test_yes_schedule_chip_detector():
    assert looks_like_yes_schedule_chip(YES_SCHEDULE_CHIP)
    assert looks_like_yes_schedule_chip(YES_SCHEDULE_CHIP_LABEL)
    assert looks_like_yes_schedule_chip("Yes, schedule")
    assert looks_like_yes_schedule_chip("yes please schedule")
    assert not looks_like_yes_schedule_chip("schedule my wedding")


def test_prior_adherence_offer_detector():
    offer = (
        "Your adherence is sitting at 86%. If you want we can dial things back "
        "for this coming week — fewer sessions, shorter gym days."
    )
    assert prior_was_adherence_schedule_offer(offer)
    assert not prior_was_adherence_schedule_offer(
        "Creatine monohydrate is evidence-backed. Want protein tips?"
    )


def test_clarifying_intake_detector():
    assert reply_asks_clarifying_intake(
        "Before I rebuild — what's your experience level, session duration, "
        "and any injuries/limitations?"
    )
    assert not reply_asks_clarifying_intake(
        "Here's a lighter 3-session week based on your history. [Memory: week of 2026-06-29]"
    )


def test_coach_routes_yes_schedule_chip_to_schedule_continuation():
    prior = (
        "Hey John — adherence is around 86% this stretch. "
        "If you want we can dial things back this week."
    )
    state = CoachingTeamState(
        user_id="demo-veteran",
        profile=_veteran_profile(),
        week_plan=_week(),
        messages=[
            HumanMessage(content="honestly this week got away from me"),
            AIMessage(content=prior),
            HumanMessage(content=YES_SCHEDULE_CHIP),
        ],
        risk_flag=False,
        coaching_team_rounds=1,
    )
    out = coach_node(state)
    assert out["intent"] == "schedule"
    assert out["proposals"].get("adherence_continuation") is True
    assert out.get("risk_flag") is False


def test_coach_short_affirm_after_adherence_offer_is_schedule():
    prior = (
        "Let's simplify your week — fewer sessions so momentum sticks. "
        "Want me to re-plan?"
    )
    state = CoachingTeamState(
        user_id="demo-veteran",
        profile=_veteran_profile(),
        week_plan=_week(),
        messages=[
            HumanMessage(content="work has been brutal"),
            AIMessage(content=prior),
            HumanMessage(content="yes please"),
        ],
    )
    out = coach_node(state)
    assert out["intent"] == "schedule"
    assert out["proposals"].get("adherence_continuation") is True


def test_coach_risk_renegotiation_with_trailing_assistant_goes_schedule():
    state = CoachingTeamState(
        user_id="demo-veteran",
        profile=_veteran_profile(),
        week_plan=_week(),
        risk_flag=True,
        coaching_team_rounds=1,
        messages=[
            HumanMessage(content="honestly this week got away from me"),
            AIMessage(content="RISK check-in — we should simplify."),
        ],
    )
    out = coach_node(state)
    assert out["intent"] == "schedule"
    assert out["proposals"].get("adherence_continuation") is True


def test_stale_risk_flag_cleared_on_fresh_human_turn():
    """Fresh human message clears stale RISK so it cannot force adherence_continuation."""
    state = CoachingTeamState(
        user_id="demo-veteran",
        profile=_veteran_profile(),
        week_plan=_week(),
        risk_flag=True,
        coaching_team_rounds=2,
        messages=[
            HumanMessage(content="honestly this week got away from me"),
            AIMessage(content="Check-in done."),
            HumanMessage(content="I have 10 minutes"),
        ],
    )
    out = coach_node(state)
    assert out.get("risk_flag") is False
    assert out["intent"] == "schedule"
    assert out["proposals"].get("micro_session") is True
    assert not out["proposals"].get("adherence_continuation")

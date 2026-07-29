"""Deterministic today/tomorrow resolution — never LLM weekday inference."""
from datetime import date

from langchain_core.messages import HumanMessage

from app.graph.agents.scheduler import scheduler_node
from app.graph.plan_utils import (
    build_informational_day_plan_reply,
    calendar_truth_block,
    looks_like_informational_day_plan_query,
    resolve_relative_day,
    workout_day_on_date,
)
from app.graph.state import CoachingTeamState, UserProfile, WeekPlan, WorkoutDay
from app.graph.supervisor import coaching_team_node


AS_OF = date(2026, 7, 29)  # Wednesday
WEEK_START = "2026-07-27"  # Monday


def _veteran_week() -> WeekPlan:
    return WeekPlan(
        week_start=WEEK_START,
        days=[
            WorkoutDay(day="Mon", focus="Upper A", duration_min=50, status="planned"),
            WorkoutDay(day="Tue", focus="Lower A", duration_min=50, status="planned"),
            WorkoutDay(day="Wed", focus="Conditioning", duration_min=35, status="planned"),
            WorkoutDay(day="Thu", focus="Upper B", duration_min=50, status="planned"),
            WorkoutDay(day="Fri", focus="Lower B", duration_min=50, status="planned"),
        ],
        calorie_target=2100,
        protein_target_g=140,
        notes="test week",
    )


def test_resolve_tomorrow_on_wednesday_is_thursday():
    r = resolve_relative_day("whats my plan for tomorrow", as_of=AS_OF)
    assert r is not None
    assert r.token == "tomorrow"
    assert r.target == date(2026, 7, 30)
    assert r.weekday_full == "Thursday"
    assert r.weekday_abbr == "Thu"


def test_resolve_today_on_wednesday_is_wednesday():
    r = resolve_relative_day("what's my plan for today", as_of=AS_OF)
    assert r is not None
    assert r.target == AS_OF
    assert r.weekday_full == "Wednesday"


def test_workout_day_on_tomorrow_matches_week_plan():
    plan = _veteran_week()
    tomorrow = date(2026, 7, 30)
    day = workout_day_on_date(plan, tomorrow)
    assert day is not None
    assert day.focus == "Upper B"
    assert day.duration_min == 50


def test_informational_reply_names_thursday_not_tuesday():
    reply = build_informational_day_plan_reply(
        profile_name="John",
        week_plan=_veteran_week(),
        user_msg="whats my plan for tomorrow",
        as_of=AS_OF,
    )
    assert reply is not None
    assert "Thursday" in reply
    assert "Tuesday" not in reply
    assert "Upper B" in reply
    assert "50" in reply


def test_adjust_request_is_not_informational_shortcut():
    msg = "yes tomorrow i only have 30 mins can you please readjust my plan accordingly"
    assert looks_like_informational_day_plan_query(msg) is False
    assert build_informational_day_plan_reply(
        profile_name="John",
        week_plan=_veteran_week(),
        user_msg=msg,
        as_of=AS_OF,
    ) is None


def test_calendar_truth_block_pins_tomorrow_thursday():
    block = calendar_truth_block(
        _veteran_week(),
        "whats my plan for tomorrow",
        as_of=AS_OF,
    )
    assert "Today is Wednesday 2026-07-29" in block
    assert "Tomorrow is Thursday 2026-07-30" in block
    assert "← TOMORROW" in block
    assert "Upper B" in block
    assert "MUST name Thursday" in block


def test_scheduler_informational_path_is_deterministic():
    state = CoachingTeamState(
        messages=[HumanMessage(content="whats my plan for tomorrow")],
        profile=UserProfile(name="John", goal="lose 8kg", sessions_per_week=5),
        week_plan=_veteran_week(),
        intent="schedule",
        proposals={},
    )
    from unittest.mock import patch

    with patch(
        "app.graph.agents.scheduler.build_informational_day_plan_reply",
        side_effect=lambda **kw: build_informational_day_plan_reply(
            **{**kw, "as_of": AS_OF}
        ),
    ):
        out = scheduler_node(state)

    assert out["proposals"].get("relative_day_info") is True
    assert out["proposals"].get("plan_changed") is False
    reply = out["proposals"]["scheduler"]
    assert "Thursday" in reply
    assert "Tuesday" not in reply
    assert "Upper B" in reply

    # coaching_team must pass the text through without re-LLM.
    merged = coaching_team_node(
        state.model_copy(update={"proposals": out["proposals"]})
    )
    assert merged["messages"][0]["content"] == reply


def test_info_and_adjust_resolve_identically():
    """Both paths must agree tomorrow == Thursday / Upper B on this as_of."""
    info = resolve_relative_day("whats my plan for tomorrow", as_of=AS_OF)
    adjust = resolve_relative_day(
        "yes tomorrow i only have 30 mins can you please readjust my plan accordingly",
        as_of=AS_OF,
    )
    assert info is not None and adjust is not None
    assert info.target == adjust.target == date(2026, 7, 30)
    assert info.weekday_full == adjust.weekday_full == "Thursday"
    plan = _veteran_week()
    assert workout_day_on_date(plan, info.target).focus == "Upper B"
    assert workout_day_on_date(plan, adjust.target).focus == "Upper B"

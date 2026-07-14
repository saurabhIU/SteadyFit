"""Routing smoke tests — no live LLM calls."""
from app.graph.build import MAX_COACHING_TEAM_ROUNDS, route_from_coach, route_from_coaching_team
from app.graph.state import CoachingTeamState


def test_route_from_coach_defaults_to_knowledge():
    assert route_from_coach(CoachingTeamState()) == "knowledge"


def test_route_from_coach_respects_intent():
    assert route_from_coach(CoachingTeamState(intent="schedule")) == "schedule"


def test_route_from_coach_intake():
    assert route_from_coach(CoachingTeamState(intent="intake")) == "intake"


def test_route_from_intake_to_scheduler_on_first_plan():
    from app.graph.build import route_from_intake
    assert route_from_intake(CoachingTeamState(intent="first_plan")) == "scheduler"
    assert route_from_intake(CoachingTeamState(intent="intake")) == "end"


def test_route_from_coaching_team_risk_loops_to_coach():
    state = CoachingTeamState(risk_flag=True, coaching_team_rounds=0)
    assert route_from_coaching_team(state) == "coach"


def test_route_from_coaching_team_plan_change_to_approve():
    state = CoachingTeamState(proposals={"plan_changed": True})
    assert route_from_coaching_team(state) == "approve"


def test_route_from_coaching_team_defaults_to_end():
    assert route_from_coaching_team(CoachingTeamState()) == "end"


def test_coaching_team_round_guard():
    state = CoachingTeamState(risk_flag=True, coaching_team_rounds=MAX_COACHING_TEAM_ROUNDS)
    assert route_from_coaching_team(state) == "end"

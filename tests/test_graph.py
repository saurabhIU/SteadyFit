"""Smoke tests for the graph topology (no LLM calls)."""
from app.graph.build import MAX_COUNCIL_ROUNDS, route_from_coach, route_from_council
from app.graph.state import CouncilState


def test_route_from_coach_defaults_to_knowledge():
    assert route_from_coach(CouncilState()) == "knowledge"


def test_route_from_coach_follows_intent():
    assert route_from_coach(CouncilState(intent="schedule")) == "schedule"


def test_route_from_council_risk_loops_to_coach():
    state = CouncilState(risk_flag=True, council_rounds=0)
    assert route_from_council(state) == "coach"


def test_route_from_council_plan_change_to_approve():
    state = CouncilState(proposals={"plan_changed": True})
    assert route_from_council(state) == "approve"


def test_route_from_council_defaults_to_end():
    assert route_from_council(CouncilState()) == "end"


def test_council_round_guard():
    state = CouncilState(risk_flag=True, council_rounds=MAX_COUNCIL_ROUNDS)
    assert route_from_council(state) == "end"

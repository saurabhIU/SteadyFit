"""Plan approval card first-plan vs tweak framing."""
from app.graph.approval_copy import has_prior_week_plan, plan_approval_framing
from app.graph.state import WeekPlan, WorkoutDay


def test_first_plan_framing_when_no_prior():
    assert has_prior_week_plan(None) is False
    assert has_prior_week_plan(WeekPlan(week_start="2026-07-14", days=[])) is False
    framing = plan_approval_framing(has_prior=False)
    assert framing["is_first_plan"] is True
    assert "first" in str(framing["headline"]).lower()
    assert "tweak" not in str(framing["headline"]).lower()


def test_tweak_framing_when_prior_exists():
    prior = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Mon", focus="Full body", duration_min=40)],
    )
    assert has_prior_week_plan(prior) is True
    framing = plan_approval_framing(has_prior=True)
    assert framing["is_first_plan"] is False
    assert "tweak" in str(framing["headline"]).lower()
    assert "first" not in str(framing["headline"]).lower()

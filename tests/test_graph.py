"""Routing smoke tests — no live LLM calls."""
from app.graph.build import MAX_COACHING_TEAM_ROUNDS, route_from_coach, route_from_coaching_team
from app.graph.critique import (
    MAX_CRITIQUE_ROUNDS,
    route_after_specialist,
    route_from_critique,
    should_critique,
)
from app.graph.state import CoachingTeamState, UserProfile


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
    state = CoachingTeamState(
        proposals={
            "plan_changed": True,
            "proposed_week_plan": {"week_start": "2026-07-14", "days": []},
        }
    )
    assert route_from_coaching_team(state) == "approve"


def test_route_from_coaching_team_plan_change_without_plan_ends():
    state = CoachingTeamState(proposals={"plan_changed": True})
    assert route_from_coaching_team(state) == "end"


def test_route_from_coaching_team_defaults_to_end():
    assert route_from_coaching_team(CoachingTeamState()) == "end"


def test_coaching_team_round_guard():
    state = CoachingTeamState(risk_flag=True, coaching_team_rounds=MAX_COACHING_TEAM_ROUNDS)
    assert route_from_coaching_team(state) == "end"


def test_should_critique_schedule_and_first_plan():
    assert should_critique(CoachingTeamState(intent="schedule", proposals={"scheduler": "x"}))
    assert should_critique(CoachingTeamState(intent="first_plan", proposals={"scheduler": "x"}))


def test_should_critique_skips_topic_interrupts():
    """Pain/allergy/pregnancy acknowledgments must not enter critique→revise."""
    from langchain_core.messages import HumanMessage

    pain = CoachingTeamState(
        intent="schedule",
        messages=[HumanMessage(content="actually my knee hurts")],
        proposals={"scheduler": "knee-safe week", "plan_changed": True},
    )
    allergy = CoachingTeamState(
        intent="nutrition",
        messages=[HumanMessage(content="also I think I'm allergic to dairy")],
        proposals={"nutrition": "dairy-free 140g protein plan", "nutrition_plan_change": True},
    )
    pregnancy = CoachingTeamState(
        intent="knowledge",
        messages=[HumanMessage(content="wait, is that safe during pregnancy?")],
        proposals={"knowledge": "pregnancy safety guidance"},
    )
    assert not should_critique(pain)
    assert not should_critique(allergy)
    assert not should_critique(pregnancy)
    assert route_after_specialist(pain) == "coaching_team"
    assert route_after_specialist(allergy) == "coaching_team"


def test_should_critique_skips_knowledge_and_adherence():
    assert not should_critique(
        CoachingTeamState(intent="knowledge", proposals={"knowledge": "RDL cues"})
    )
    assert not should_critique(
        CoachingTeamState(intent="adherence", proposals={"adherence": "RISK lighten week"})
    )


def test_should_critique_nutrition_plan_change_flag():
    assert should_critique(
        CoachingTeamState(
            intent="nutrition",
            proposals={"nutrition": "ok", "nutrition_plan_change": True},
        )
    )
    assert not should_critique(
        CoachingTeamState(intent="nutrition", proposals={"nutrition": "try greek yogurt"})
    )


def test_route_after_specialist_to_critique_or_merge():
    assert (
        route_after_specialist(CoachingTeamState(intent="schedule", proposals={"scheduler": "p"}))
        == "critique"
    )
    assert (
        route_after_specialist(CoachingTeamState(intent="knowledge", proposals={"knowledge": "p"}))
        == "coaching_team"
    )


def test_route_from_critique_revises_then_merges():
    revise = CoachingTeamState(
        intent="schedule",
        proposals={
            "scheduler": "heavy back squat week",
            "revision_instructions": "Avoid deep loaded squats for knee constraint.",
        },
        critique_rounds=1,
    )
    assert route_from_critique(revise) == "scheduler"

    done = CoachingTeamState(
        intent="schedule",
        proposals={"scheduler": "knee-safe week"},
        critique_rounds=1,
    )
    assert route_from_critique(done) == "coaching_team"


def test_critique_cap_constant_separate_from_risk():
    assert MAX_CRITIQUE_ROUNDS == 1
    assert MAX_COACHING_TEAM_ROUNDS == 2


def test_critique_soft_nitpick_coerced_to_clean(monkeypatch):
    from app.graph import critique as critique_mod

    monkeypatch.setattr(
        critique_mod,
        "_run_critique_llm",
        lambda **_kwargs: {
            "verdict": "revise",
            "critique": "The protein target of 140g may be unrealistic without meal examples.",
            "revision_triggered": True,
            "specialist": "scheduler",
        },
    )
    state = CoachingTeamState(
        intent="schedule",
        profile=UserProfile(name="Saurabh", goal="lose fat", sessions_per_week=3, onboarding_complete=True),
        proposals={"scheduler": "light Thursday walk week with 1900 kcal / 140g protein"},
    )
    out = critique_mod.critique_node(state)
    assert out["critique_verdict"] == "clean"
    assert "revision_instructions" not in out["proposals"]
    assert out.get("coaching_team_transcript") in (None, [],) or "coaching_team_transcript" not in out


def test_critique_hard_knee_failure_still_revises(monkeypatch):
    from app.graph import critique as critique_mod

    monkeypatch.setattr(
        critique_mod,
        "_run_critique_llm",
        lambda **_kwargs: {
            "verdict": "revise",
            "critique": "Heavy back squats contradict the left knee constraint.",
            "revision_triggered": True,
            "specialist": "scheduler",
        },
    )
    state = CoachingTeamState(
        intent="schedule",
        profile=UserProfile(
            name="Saurabh",
            goal="lose fat",
            constraints=["left knee pain — avoid deep loaded squats"],
            onboarding_complete=True,
        ),
        proposals={"scheduler": "Heavy back squat 5x5 every day"},
    )
    out = critique_mod.critique_node(state)
    assert out["critique_verdict"] == "revise"
    assert out["critique_rounds"] == 1
    assert out["proposals"]["revision_instructions"]


def test_critique_node_second_pass_caps_without_loop(monkeypatch):
    """Even if the LLM would revise again, second pass always merges."""
    from app.graph import critique as critique_mod

    calls = {"n": 0}

    def boom(**_kwargs):
        calls["n"] += 1
        return {"verdict": "revise", "critique": "still wrong", "revision_triggered": True}

    monkeypatch.setattr(critique_mod, "_run_critique_llm", boom)

    state = CoachingTeamState(
        intent="schedule",
        profile=UserProfile(
            name="Saurabh",
            goal="lose fat",
            constraints=["left knee — avoid deep loaded squats"],
            onboarding_complete=True,
        ),
        proposals={"scheduler": "still includes back squat 5x5"},
        critique_rounds=1,
        coaching_team_transcript=[
            {"type": "proposal", "agent": "scheduler", "text": "original"},
            {"type": "critique", "agent": "coach", "text": "knee contraindication"},
        ],
    )
    out = critique_mod.critique_node(state)
    assert calls["n"] == 0  # no second LLM call
    assert out["critique_verdict"] == "revise_capped"
    assert "revision_instructions" not in out["proposals"]
    assert any(e["type"] == "revision" for e in out["coaching_team_transcript"])
    merged = CoachingTeamState(
        intent="schedule",
        proposals=out["proposals"],
        critique_rounds=out["critique_rounds"],
    )
    assert route_from_critique(merged) == "coaching_team"

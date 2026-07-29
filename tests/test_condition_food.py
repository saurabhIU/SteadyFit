"""Diabetes/hypertension food-logging nudge — narrow, deterministic feature.

Covers:
- classify_food_conditions / build_condition_nudge unit behavior
- nutrition_node integration: diabetes-only + hypertension-only eval cases
- confirms the nudge never touches plan_changed / coaching_team routing
"""
from __future__ import annotations

from unittest.mock import patch

from langchain_core.messages import HumanMessage

from app.graph.condition_food import (
    DIABETES,
    HYPERTENSION,
    build_condition_nudge,
    classify_food_conditions,
)
from app.graph.personalization import PersonalPlanContext
from app.graph.state import CoachingTeamState, UserProfile
from app.graph.tool_agent import ToolAgentResult

FAKE_DIABETES_CITE = {
    "source_file": "Obesity_Diabetes_Office.md",
    "section": "Nutrition Timing for Diabetics",
    "kb_id": None,
    "snippet": "glycaemic_index: Prefer low GI foods: oats, legumes, most fruits, vegetables",
    "tag": "[KB: Obesity_Diabetes_Office.md — Nutrition Timing for Diabetics]",
}
FAKE_HYPERTENSION_CITE = {
    "source_file": "Obesity_Diabetes_Office.md",
    "section": "Nutrition Notes (Practical, Non-Clinical)",
    "kb_id": None,
    "snippet": "sodium_awareness: Favour whole foods; go easy on heavily salted restaurant meals",
    "tag": "[KB: Obesity_Diabetes_Office.md — Nutrition Notes (Practical, Non-Clinical)]",
}


def _fake_retrieve_kb(query, **kwargs):
    if "diabetes" in query.lower() or "glycemic" in query.lower():
        return (["chunk"], [FAKE_DIABETES_CITE])
    return (["chunk"], [FAKE_HYPERTENSION_CITE])


# ── classify_food_conditions ────────────────────────────────────────────────

def test_classify_diabetes_only_flags_donut():
    assert classify_food_conditions("chocolate donut", [DIABETES]) == [DIABETES]


def test_classify_hypertension_only_flags_processed_food():
    assert classify_food_conditions("bacon and sausage", [HYPERTENSION]) == [HYPERTENSION]


def test_classify_combined_flags_both_for_salty_pastry():
    risks = classify_food_conditions(
        "a salty processed pastry", [DIABETES, HYPERTENSION]
    )
    assert set(risks) == {DIABETES, HYPERTENSION}


def test_classify_no_flag_for_balanced_meal():
    assert classify_food_conditions("grilled chicken and rice", [DIABETES, HYPERTENSION]) == []


def test_classify_ignores_condition_not_noted_by_user():
    # Food matches the sugar pattern, but user only has hypertension noted.
    assert classify_food_conditions("chocolate donut", [HYPERTENSION]) == []


def test_classify_empty_when_no_conditions():
    assert classify_food_conditions("chocolate donut", []) == []


# ── build_condition_nudge ────────────────────────────────────────────────────

def test_build_nudge_diabetes_only_wording_and_citation():
    with patch("app.rag.retriever.retrieve_kb", side_effect=_fake_retrieve_kb):
        msg, cites = build_condition_nudge([DIABETES])
    assert "diabetes" in msg.lower()
    assert "spike blood sugar" in msg.lower()
    assert "hypertension" not in msg.lower()
    assert "sodium" not in msg.lower()
    assert FAKE_DIABETES_CITE["tag"] in msg
    assert cites == [FAKE_DIABETES_CITE]


def test_build_nudge_hypertension_only_wording_and_citation():
    with patch("app.rag.retriever.retrieve_kb", side_effect=_fake_retrieve_kb):
        msg, cites = build_condition_nudge([HYPERTENSION])
    assert "hypertension" in msg.lower()
    assert "sodium" in msg.lower()
    assert "blood sugar" not in msg.lower()
    assert FAKE_HYPERTENSION_CITE["tag"] in msg
    assert cites == [FAKE_HYPERTENSION_CITE]


def test_build_nudge_combined_is_one_headsup_line_not_two():
    with patch("app.rag.retriever.retrieve_kb", side_effect=_fake_retrieve_kb):
        msg, cites = build_condition_nudge([DIABETES, HYPERTENSION])
    # Exactly one "Since you've noted" heads-up clause, not two stacked warnings.
    assert msg.count("Since you've noted") == 1
    assert "diabetes and hypertension" in msg.lower()
    assert FAKE_DIABETES_CITE["tag"] in msg
    assert FAKE_HYPERTENSION_CITE["tag"] in msg
    assert len(cites) == 2


def test_build_nudge_falls_back_to_static_citation_on_kb_error():
    with patch("app.rag.retriever.retrieve_kb", side_effect=RuntimeError("db down")):
        msg, cites = build_condition_nudge([DIABETES])
    assert "Obesity_Diabetes_Office.md" in cites[0]["source_file"]
    assert "[KB:" in msg


def test_build_nudge_empty_risks_is_noop():
    msg, cites = build_condition_nudge([])
    assert msg == ""
    assert cites == []


def test_build_nudge_no_numbers_no_clinical_claims():
    with patch("app.rag.retriever.retrieve_kb", side_effect=_fake_retrieve_kb):
        msg, _ = build_condition_nudge([DIABETES, HYPERTENSION])
    for banned in ("mmol", "mg/dl", "systolic", "diastolic", "hba1c", "diagnos"):
        assert banned not in msg.lower()


# ── nutrition_node integration (the two required eval cases) ───────────────

def _state_for(message: str, user_id: str = "u-cond") -> CoachingTeamState:
    return CoachingTeamState(
        profile=UserProfile(goal="lose fat", onboarding_complete=True),
        messages=[HumanMessage(content=message)],
        user_id=user_id,
    )


def test_eval_diabetes_only_profile_logs_donut_flagged():
    """Diabetes-only profile logs a donut → flagged (diabetes framing only) +

    KB-grounded lower-GI suggestion + citation.
    """
    from app.graph.agents import nutrition as nutrition_mod

    fake_reply = ToolAgentResult(
        text="Chocolate donut logged — ~271 kcal, 3g protein, 34g carbs, 15g fat.",
        tools_called=["log_food_entry"],
        tool_outputs=["{}"],
    )
    ctx = PersonalPlanContext(has_docs=True, health_conditions=[DIABETES])
    with (
        patch.object(nutrition_mod, "run_tool_agent", return_value=fake_reply),
        patch.object(nutrition_mod, "load_personal_plan_context", return_value=ctx),
        patch("app.rag.retriever.retrieve_kb", side_effect=_fake_retrieve_kb),
    ):
        out = nutrition_mod.nutrition_node(
            _state_for("I ate a chocolate donut for breakfast")
        )

    reply = out["proposals"]["nutrition"]
    assert "diabetes" in reply.lower()
    assert "spike blood sugar" in reply.lower()
    # Diabetes framing only — no hypertension/sodium language leaking in.
    assert "hypertension" not in reply.lower()
    assert "sodium" not in reply.lower()
    assert FAKE_DIABETES_CITE["tag"] in reply
    assert any(
        c.get("source_file") == "Obesity_Diabetes_Office.md" for c in out["citations"]
    )
    # Still logged normally — no refusal/blocking.
    assert "kcal" in reply.lower()
    # Meal logging never a plan-change / coaching-team event.
    assert out["proposals"].get("meal_log_only") is True
    assert "nutrition_plan_change" not in out["proposals"]
    assert "plan_changed" not in out["proposals"]


def test_eval_hypertension_only_profile_logs_salty_food_flagged():
    """Hypertension-only profile logs a salty processed food → flagged

    (hypertension framing only) + KB-grounded lower-sodium suggestion + citation.
    """
    from app.graph.agents import nutrition as nutrition_mod

    fake_reply = ToolAgentResult(
        text="Bacon and sausage logged — ~410 kcal, 22g protein, 2g carbs, 34g fat.",
        tools_called=["log_food_entry"],
        tool_outputs=["{}"],
    )
    ctx = PersonalPlanContext(has_docs=True, health_conditions=[HYPERTENSION])
    with (
        patch.object(nutrition_mod, "run_tool_agent", return_value=fake_reply),
        patch.object(nutrition_mod, "load_personal_plan_context", return_value=ctx),
        patch("app.rag.retriever.retrieve_kb", side_effect=_fake_retrieve_kb),
    ):
        out = nutrition_mod.nutrition_node(
            _state_for("I had bacon and sausage for breakfast")
        )

    reply = out["proposals"]["nutrition"]
    assert "hypertension" in reply.lower()
    assert "sodium" in reply.lower()
    # Hypertension framing only — no diabetes/blood-sugar language leaking in
    # (the KB filename itself contains "Diabetes", so check the framing text,
    # not a raw substring match against the whole reply).
    assert "since you've noted diabetes" not in reply.lower()
    assert "blood sugar" not in reply.lower()
    assert FAKE_HYPERTENSION_CITE["tag"] in reply
    assert any(
        c.get("source_file") == "Obesity_Diabetes_Office.md" for c in out["citations"]
    )
    assert "kcal" in reply.lower()
    assert out["proposals"].get("meal_log_only") is True
    assert "nutrition_plan_change" not in out["proposals"]
    assert "plan_changed" not in out["proposals"]


def test_no_nudge_when_no_conditions_noted():
    """No docs / no conditions → behavior unchanged from today."""
    from app.graph.agents import nutrition as nutrition_mod

    fake_reply = ToolAgentResult(
        text="Chocolate donut logged — ~271 kcal.",
        tools_called=["log_food_entry"],
        tool_outputs=["{}"],
    )
    ctx = PersonalPlanContext(has_docs=False, health_conditions=[])
    with (
        patch.object(nutrition_mod, "run_tool_agent", return_value=fake_reply),
        patch.object(nutrition_mod, "load_personal_plan_context", return_value=ctx),
    ):
        out = nutrition_mod.nutrition_node(
            _state_for("I ate a chocolate donut for breakfast")
        )
    reply = out["proposals"]["nutrition"]
    assert reply == fake_reply.text
    assert "diabetes" not in reply.lower()
    assert "hypertension" not in reply.lower()


def test_no_nudge_when_food_does_not_match_pattern():
    """Diabetes noted, but a balanced meal shouldn't trigger the nudge."""
    from app.graph.agents import nutrition as nutrition_mod

    fake_reply = ToolAgentResult(
        text="Grilled chicken and rice logged — ~450 kcal.",
        tools_called=["log_food_entry"],
        tool_outputs=["{}"],
    )
    ctx = PersonalPlanContext(has_docs=True, health_conditions=[DIABETES])
    with (
        patch.object(nutrition_mod, "run_tool_agent", return_value=fake_reply),
        patch.object(nutrition_mod, "load_personal_plan_context", return_value=ctx),
    ):
        out = nutrition_mod.nutrition_node(
            _state_for("I ate grilled chicken and rice for lunch")
        )
    reply = out["proposals"]["nutrition"]
    assert reply == fake_reply.text
    assert "diabetes" not in reply.lower()

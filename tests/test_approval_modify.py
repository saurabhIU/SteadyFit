"""Pending plan-approval: free-text resumes as modify, then re-enters the graph."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from langgraph.types import Command

from app.chat_pipeline import process_user_chat
from app.graph.state import CoachingTeamState, UserProfile, WeekPlan, WorkoutDay
from app.graph.supervisor import approve_node


def _state_with_proposal(*, prior: WeekPlan | None, proposed: WeekPlan) -> CoachingTeamState:
    return CoachingTeamState(
        user_id="demo-veteran",
        profile=UserProfile(name="John", goal="build muscle", sessions_per_week=4),
        week_plan=prior,
        proposals={
            "scheduler": "draft week",
            "plan_changed": True,
            "proposed_week_plan": proposed.model_dump(),
        },
    )


def test_approve_node_modify_promotes_proposed_plan_without_message():
    proposed = WeekPlan(
        week_start="2026-07-14",
        days=[
            WorkoutDay(day="Mon", focus="Upper", duration_min=40, status="planned"),
            WorkoutDay(day="Wed", focus="Lower", duration_min=40, status="planned"),
            WorkoutDay(day="Fri", focus="Zone 2", duration_min=30, status="planned"),
        ],
        calorie_target=2100,
        protein_target_g=140,
        notes="draft",
    )
    prior = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Mon", focus="Full body", duration_min=45, status="planned")],
        calorie_target=2200,
        protein_target_g=150,
    )
    real = _state_with_proposal(prior=prior, proposed=proposed)
    with (
        patch(
            "app.graph.supervisor._ensure_personalization_on_plan_change",
            side_effect=lambda s: dict(s.proposals),
        ),
        patch("app.graph.supervisor.interrupt", return_value="modify"),
        patch("app.memory.store.get_saved_week_plan", return_value=prior),
    ):
        out = approve_node(real)

    assert out["week_plan"].days[0].focus == "Upper"
    assert len(out["week_plan"].days) == 3
    assert out["proposals"] == {}
    assert "messages" not in out  # silent — next chat turn owns the reply


def test_approve_node_reject_still_keeps_prior_copy():
    proposed = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Mon", focus="Upper", duration_min=40, status="planned")],
    )
    prior = WeekPlan(
        week_start="2026-07-14",
        days=[WorkoutDay(day="Tue", focus="Lower", duration_min=45, status="planned")],
    )
    real = _state_with_proposal(prior=prior, proposed=proposed)
    with (
        patch(
            "app.graph.supervisor._ensure_personalization_on_plan_change",
            side_effect=lambda s: dict(s.proposals),
        ),
        patch("app.graph.supervisor.interrupt", return_value="reject"),
        patch("app.memory.store.get_saved_week_plan", return_value=prior),
    ):
        out = approve_node(real)
    assert "week_plan" not in out
    assert "kept your previous plan" in out["messages"][0]["content"].lower()


def test_chat_pipeline_sounds_good_returns_short_confirm_not_proposal_body():
    pending = {
        "type": "plan_approval",
        "proposed_plan": {"week_start": "2026-07-14", "days": []},
        "is_first_plan": False,
        "personalization_note": (
            "I see you've uploaded a personal document — I've factored it into this plan."
        ),
    }
    graph = MagicMock()
    graph.invoke.return_value = {
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "I see you've uploaded a personal document — I've factored it into this plan.\n\n"
                    "Here's the update — take a look below."
                ),
            }
        ],
    }
    graph.get_state.return_value = MagicMock(values={}, interrupts=())

    with (
        patch("app.chat_pipeline._pending_approval", return_value=pending),
        patch("app.chat_pipeline._snapshot_messages", return_value=[]),
        patch("app.chat_pipeline.get_profile") as gp,
        patch("app.chat_pipeline.build_chat_payload") as bcp,
        patch("app.chat_pipeline.persist_approved_plan"),
    ):
        gp.return_value = MagicMock(
            onboarding_complete=True,
            awaiting_onboarding_confirm=False,
            awaiting_weight_for_first_plan=False,
            awaiting_diet_slot=None,
            awaiting_upload_before_weight=False,
        )
        # Simulate a buggy last_message_content still pointing at the proposal.
        bcp.return_value = {
            "thread_id": "demo-veteran:t1",
            "reply": (
                "I see you've uploaded a personal document — I've factored it into this plan.\n\n"
                "Here's the update — take a look below."
            ),
            "coaching_team": {"scheduler": "draft"},
            "pending_approval": pending,
            "quick_replies": [],
            "citations": [],
        }
        out = process_user_chat(
            graph, "sounds good", user_id="demo-veteran", thread_id="t1"
        )

    assert out["reply"] == "Plan approved and saved — you're set for the week."
    assert out["pending_approval"] is None
    assert out["coaching_team"] == {}
    assert "look below" not in out["reply"].lower()
    assert "personal document" not in out["reply"].lower()
    assert isinstance(graph.invoke.call_args.args[0], Command)
    assert graph.invoke.call_args.args[0].resume == "accept"


def test_chat_pipeline_pending_free_text_resumes_modify_then_enters_graph():
    proposed = {
        "week_start": "2026-07-14",
        "days": [
            {"day": "Mon", "focus": "Upper", "duration_min": 40, "status": "planned"},
            {"day": "Wed", "focus": "Lower", "duration_min": 40, "status": "planned"},
            {"day": "Fri", "focus": "Zone 2", "duration_min": 30, "status": "planned"},
        ],
    }
    pending = {"type": "plan_approval", "proposed_plan": proposed, "is_first_plan": False}
    graph = MagicMock()
    invoke_calls: list = []

    def _invoke(arg, config=None):
        invoke_calls.append(arg)
        if isinstance(arg, Command):
            return {"messages": []}
        return {
            "messages": [{"role": "assistant", "content": "Updated draft — 2 sessions."}],
        }

    graph.invoke.side_effect = _invoke
    graph.get_state.return_value = MagicMock(
        values={"messages": [], "week_plan": None},
        interrupts=(),
    )

    with (
        patch("app.chat_pipeline._pending_approval", return_value=pending),
        patch("app.chat_pipeline._snapshot_messages", return_value=[]),
        patch("app.chat_pipeline.get_profile") as gp,
        patch("app.chat_pipeline.build_chat_payload") as bcp,
        patch("app.chat_pipeline.bootstrap_input") as boot,
    ):
        gp.return_value = MagicMock(
            onboarding_complete=True,
            awaiting_onboarding_confirm=False,
            awaiting_weight_for_first_plan=False,
            awaiting_diet_slot=None,
            awaiting_upload_before_weight=False,
        )
        boot.return_value = {"messages": [{"role": "user", "content": "reduce to 2 sessions"}]}
        bcp.return_value = {
            "thread_id": "demo-veteran:t1",
            "reply": "Updated draft — 2 sessions.",
            "coaching_team": {},
            "pending_approval": {
                "type": "plan_approval",
                "proposed_plan": {
                    "week_start": "2026-07-14",
                    "days": [
                        {"day": "Mon", "focus": "Upper", "duration_min": 40},
                        {"day": "Thu", "focus": "Lower", "duration_min": 40},
                    ],
                },
            },
            "quick_replies": [],
            "citations": [],
        }

        out = process_user_chat(
            graph,
            "reduce to 2 sessions this week",
            user_id="demo-veteran",
            thread_id="t1",
        )

    assert len(invoke_calls) == 2
    assert isinstance(invoke_calls[0], Command)
    assert invoke_calls[0].resume == "modify"
    assert out["pending_approval"]["type"] == "plan_approval"
    assert "still waiting" not in (out.get("reply") or "").lower()
    assert out["scope"] == "bypassed_pending_state"

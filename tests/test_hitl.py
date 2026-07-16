"""Tests for plan parsing and API response helpers."""
from langgraph.types import Interrupt

from app.graph.plan_utils import parse_week_plan
from app.graph.response import (
    build_chat_payload,
    build_thread_history,
    pending_approval_from_interrupts,
    proposals_from_state,
)


SAMPLE = """Here's a lighter week while you travel.

```json
{
  "week_start": "2026-07-14",
  "days": [
    {"day": "Mon", "focus": "Upper push", "duration_min": 40, "status": "planned"},
    {"day": "Wed", "focus": "Lower", "duration_min": 35, "status": "planned"}
  ],
  "calorie_target": 2100,
  "protein_target_g": 140,
  "notes": "Travel-friendly"
}
```"""


NESTED_WITH_TOOL_NOISE = """
Looking at {"kb_id": "tmpl_007"} for hotel week.

```json
{
  "week_start": "2026-07-14",
  "days": [
    {"day": "Mon", "focus": "Push-Up (chest_010)", "duration_min": "40", "status": "planned"},
    {"day": "Wed", "focus": "Goblet squat (legs_002)", "duration_min": 35}
  ],
  "calorie_target": 2100,
  "protein_target_g": 140,
  "notes": "hotel bodyweight"
}
```
"""


def test_parse_week_plan_from_fenced_json():
    plan = parse_week_plan(SAMPLE)
    assert plan is not None
    assert plan.week_start == "2026-07-14"
    assert len(plan.days) == 2
    assert plan.days[0].focus == "Upper push"
    assert plan.calorie_target == 2100


def test_parse_week_plan_nested_json_despite_tool_noise():
    plan = parse_week_plan(NESTED_WITH_TOOL_NOISE)
    assert plan is not None
    assert len(plan.days) == 2
    assert plan.days[0].duration_min == 40
    assert plan.days[1].status == "planned"


def test_coerce_week_plan_from_dict():
    from app.graph.plan_utils import coerce_week_plan

    plan = coerce_week_plan(
        {
            "week_start": "2026-07-14",
            "days": [{"day": "Mon", "focus": "Push", "duration_min": 40}],
        }
    )
    assert plan is not None
    assert plan.days[0].focus == "Push"


def test_coerce_week_plan_rejects_missing_week_start():
    from app.graph.plan_utils import coerce_week_plan

    assert coerce_week_plan({"days": [{"day": "Mon", "focus": "Push"}]}) is None


def test_pending_approval_from_interrupt():
    payload = {
        "type": "plan_approval",
        "proposed_plan": {"week_start": "2026-07-14", "days": []},
        "scheduler_summary": "Move leg day to Friday",
    }
    pending = pending_approval_from_interrupts([Interrupt(value=payload)])
    assert pending == payload


def test_build_chat_payload_with_interrupt_only_result():
    state = {
        "messages": [{"role": "assistant", "content": "Here's your adjusted week."}],
        "proposals": {
            "scheduler": "moved sessions",
            "plan_changed": True,
            "proposed_week_plan": {"week_start": "2026-07-14", "days": []},
        },
    }

    class FakeGraph:
        def get_state(self, _config):
            class Snapshot:
                values = state

            return Snapshot()

    payload = {
        "type": "plan_approval",
        "proposed_plan": {"week_start": "2026-07-14", "days": []},
        "scheduler_summary": "moved sessions",
    }
    result = {"__interrupt__": [Interrupt(value=payload)]}
    out = build_chat_payload(
        "thread-1",
        result,
        graph=FakeGraph(),
        config={"configurable": {"thread_id": "thread-1"}},
    )
    assert out["thread_id"] == "thread-1"
    assert out["reply"] == "Here's your adjusted week."
    assert out["pending_approval"] == payload
    assert "plan_changed" not in out["coaching_team"]
    assert "proposed_week_plan" not in out["coaching_team"]


def test_build_thread_history_restores_messages_and_pending():
    state = {
        "messages": [
            {"role": "user", "content": "I missed leg day"},
            {"role": "assistant", "content": "Let's move it to Friday."},
        ],
        "proposals": {"scheduler": "moved leg day", "plan_changed": True},
    }
    payload = {
        "type": "plan_approval",
        "proposed_plan": {"week_start": "2026-07-14", "days": []},
        "scheduler_summary": "moved leg day",
    }

    class FakeGraph:
        def get_state(self, _config):
            class Snapshot:
                values = state
                interrupts = (Interrupt(value=payload),)

            return Snapshot()

    out = build_thread_history(FakeGraph(), "thread-1")
    assert len(out["messages"]) == 2
    assert out["messages"][0]["content"] == "I missed leg day"
    assert "coaching_team" not in out["messages"][1]
    assert out["pending_approval"] == payload


def test_build_thread_history_skips_system_trigger():
    state = {
        "messages": [
            {"role": "user", "content": "SYSTEM_TRIGGER: weekly review"},
            {"role": "assistant", "content": "Here is your week."},
        ],
        "proposals": {},
    }

    class FakeGraph:
        def get_state(self, _config):
            class Snapshot:
                values = state
                interrupts = ()

            return Snapshot()

    out = build_thread_history(FakeGraph(), "weekly-review")
    assert len(out["messages"]) == 1
    assert out["messages"][0]["role"] == "assistant"


def test_proposals_from_state_strips_internal_keys():
    proposals = proposals_from_state(
        {"proposals": {"scheduler": "ok", "plan_changed": True, "proposed_week_plan": {}}}
    )
    assert proposals == {"scheduler": "ok"}

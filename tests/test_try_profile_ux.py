"""Calendar tool + plan-approval reply sanitizer."""
from app.graph.supervisor import _sanitize_plan_change_reply
from app.tools.calendar_tool import get_calendar_conflicts


def test_calendar_conflicts_empty_by_default():
    assert get_calendar_conflicts() == []
    assert get_calendar_conflicts("demo-user") == []
    assert get_calendar_conflicts("try-abcdef12") == []


def test_sanitize_strips_reply_approve_and_adds_look_below():
    raw = (
        "Here's a 3-day week at ~1800 kcal. "
        "Reply approve to lock it in when you're ready."
    )
    out = _sanitize_plan_change_reply(raw, plan_changed=True)
    assert "reply approve" not in out.lower()
    assert "look below" in out.lower() or "take a look" in out.lower()


def test_sanitize_noop_when_no_plan_change():
    raw = "Reply approve if you like creatine."
    out = _sanitize_plan_change_reply(raw, plan_changed=False)
    assert "look below" not in out.lower()

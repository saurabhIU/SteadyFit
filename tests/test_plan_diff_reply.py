"""Unit tests for diff-based plan_changed reply composition."""
from datetime import date

from langchain_core.messages import HumanMessage

from app.graph.plan_diff import compute_plan_diff, format_plan_diff_reply
from app.graph.state import CoachingTeamState, UserProfile, WeekPlan, WorkoutDay
from app.graph.supervisor import _plan_change_intro, coaching_team_node


AS_OF = date(2026, 7, 29)  # Wednesday → tomorrow Thursday
WEEK_START = "2026-07-27"


def _prior() -> WeekPlan:
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
    )


def _proposed_thu_30() -> WeekPlan:
    return WeekPlan(
        week_start=WEEK_START,
        days=[
            WorkoutDay(
                day="Mon",
                focus="Upper A — Barbell bench press, seated cable row",
                duration_min=50,
                status="planned",
            ),
            WorkoutDay(
                day="Tue",
                focus="Lower A — Leg press, RDL",
                duration_min=50,
                status="planned",
            ),
            WorkoutDay(
                day="Wed",
                focus="Conditioning — Brisk walk",
                duration_min=35,
                status="planned",
            ),
            WorkoutDay(
                day="Thu",
                focus="Upper B — Flat dumbbell press [30-min express]",
                duration_min=30,
                status="planned",
            ),
            WorkoutDay(
                day="Fri",
                focus="Lower B — Goblet squat, RDL",
                duration_min=50,
                status="planned",
            ),
        ],
        calorie_target=2076,
        protein_target_g=140,
    )


def test_diff_marks_thursday_duration_as_requested():
    msg = "yes tomorrow i only have 30 mins can you please readjust my plan accordingly"
    diff = compute_plan_diff(
        _prior(),
        _proposed_thu_30(),
        user_msg=msg,
        citations=[
            {
                "tag": "[Memory: week of 2026-06-29]",
                "kind": "memory",
                "source_file": "week_2026-06-29",
            }
        ],
        as_of=AS_OF,
    )
    assert any(c.requested and c.weekday_full == "Thursday" for c in diff.changes)
    thu = next(c for c in diff.changes if c.weekday_full == "Thursday")
    assert thu.new_duration == 30
    assert thu.old_duration == 50
    # Detail rewrites on other days are secondary
    secondary = [c for c in diff.changes if not c.requested]
    assert all(c.weekday_full != "Thursday" for c in secondary)
    assert "[Memory: week of 2026-06-29]" in diff.memory_tags


def test_format_reply_names_thursday_and_30_and_memory():
    msg = "yes tomorrow i only have 30 mins can you please readjust my plan accordingly"
    diff = compute_plan_diff(
        _prior(),
        _proposed_thu_30(),
        user_msg=msg,
        citations=[{"tag": "[Memory: week of 2026-06-29]", "kind": "memory"}],
        as_of=AS_OF,
    )
    reply = format_plan_diff_reply(diff, modes=["gym"], goal="lose 8kg")
    assert "Thursday" in reply
    assert "30" in reply
    assert "I've adjusted this week around" not in reply  # no vague template
    assert "[Memory: week of 2026-06-29]" in reply
    # Secondary detail line may mention other days
    assert "take a look below" in reply.lower() or "look below" in reply.lower()


def test_plan_change_intro_uses_diff():
    state = CoachingTeamState(
        user_id="demo-veteran",
        profile=UserProfile(
            name="John",
            goal="lose 8kg",
            preferred_workout_modes=["gym", "walking"],
            onboarding_complete=True,
        ),
        week_plan=_prior(),
        messages=[
            HumanMessage(
                content="yes tomorrow i only have 30 mins can you please readjust my plan accordingly"
            )
        ],
        proposals={
            "plan_changed": True,
            "proposed_week_plan": _proposed_thu_30().model_dump(),
        },
        citations=[{"tag": "[Memory: week of 2026-07-13]", "kind": "memory"}],
    )
    # Pin as_of via patching resolve inside compute — call format path through intro
    from unittest.mock import patch

    with patch("app.graph.plan_diff.resolve_relative_day") as mock_res:
        from app.graph.plan_utils import ResolvedRelativeDay

        mock_res.return_value = ResolvedRelativeDay(
            token="tomorrow",
            target=date(2026, 7, 30),
            weekday_full="Thursday",
            weekday_abbr="Thu",
            offset_days=1,
        )
        intro = _plan_change_intro(state)
    assert "Thursday" in intro
    assert "30" in intro
    assert "[Memory: week of 2026-07-13]" in intro


def test_coaching_team_api_reply_field_is_concrete():
    state = CoachingTeamState(
        user_id="u-diff",
        profile=UserProfile(
            name="John",
            goal="lose 8kg",
            preferred_workout_modes=["gym"],
            onboarding_complete=True,
        ),
        week_plan=_prior(),
        messages=[
            HumanMessage(
                content="yes tomorrow i only have 30 mins can you please readjust my plan accordingly"
            )
        ],
        proposals={
            "plan_changed": True,
            "proposed_week_plan": _proposed_thu_30().model_dump(),
            "personalization_note": "I see you've uploaded a personal document — I've factored it into this plan.",
        },
        citations=[{"tag": "[Memory: week of 2026-06-29]", "kind": "memory"}],
    )
    from unittest.mock import patch
    from app.graph.plan_utils import ResolvedRelativeDay

    with patch("app.graph.plan_diff.resolve_relative_day") as mock_res:
        mock_res.return_value = ResolvedRelativeDay(
            token="tomorrow",
            target=date(2026, 7, 30),
            weekday_full="Thursday",
            weekday_abbr="Thu",
            offset_days=1,
        )
        out = coaching_team_node(state)
    reply = out["messages"][0]["content"]
    assert "Thursday" in reply
    assert "30" in reply
    assert "[Memory: week of 2026-06-29]" in reply
    assert "uploaded a personal document" in reply

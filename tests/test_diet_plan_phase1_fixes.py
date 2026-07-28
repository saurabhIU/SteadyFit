"""Phase-1 diet-plan fixes: week_start, cuisine default, intro vs card, persist."""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from app.graph.diet_plan import build_diet_week, wants_indian_cuisine
from app.graph.plan_utils import current_week_monday, current_week_start_iso
from app.graph.state import CoachingTeamState, UserProfile, WeekPlan, WorkoutDay
from app.graph.supervisor import _plan_change_intro


def test_current_week_start_is_monday():
    # 2026-07-27 is a Monday
    assert current_week_monday(date(2026, 7, 27)) == date(2026, 7, 27)
    # Wednesday → that week's Monday
    assert current_week_monday(date(2026, 7, 29)) == date(2026, 7, 27)
    assert current_week_start_iso(date(2026, 7, 29)) == "2026-07-27"


def test_neutral_meals_by_default_no_indian_markers():
    profile = UserProfile(
        food_preference="no-preference",
        goal="lose fat",
    )
    meals = build_diet_week(profile, week_start="2026-07-27")
    blob = " ".join(m["food_description"].lower() for m in meals)
    for marker in ("dal", "roti", "paneer", "rajma", "chole", "dahi"):
        assert marker not in blob, f"unexpected Indian marker {marker!r} in {blob}"
    assert meals[0].get("cuisine") == "neutral"


def test_indian_meals_when_conversation_signals():
    profile = UserProfile(food_preference="vegetarian", goal="lose fat")
    assert wants_indian_cuisine(profile, conversation_text="I love dal and roti")
    meals = build_diet_week(
        profile,
        week_start="2026-07-27",
        conversation_text="Keep it Indian — dal and roti are fine",
    )
    blob = " ".join(m["food_description"].lower() for m in meals)
    assert any(m in blob for m in ("dal", "roti", "paneer", "rajma", "chole", "dahi"))
    assert meals[0].get("cuisine") == "indian"


def test_plan_change_intro_has_no_day_by_day():
    state = CoachingTeamState(
        profile=UserProfile(
            goal="lose fat",
            preferred_workout_modes=["walking", "gym"],
            onboarding_complete=True,
        ),
        week_plan=None,
        proposals={"plan_changed": True},
    )
    with patch("app.memory.store.get_saved_week_plan", return_value=None):
        text = _plan_change_intro(state)
    assert "take a look below" in text.lower()
    for day in ("Mon", "Tue", "Wed", "Thu", "Fri", "breakfast", "lunch", "dinner"):
        assert day not in text
    # Should not dump a schedule
    assert text.count("\n") <= 3


def test_replace_diet_plan_week_then_query_by_plan_week_start():
    from app.memory import store as store_mod

    uid = "eval-diet-persist"
    week_start = current_week_start_iso()
    meals = build_diet_week(
        UserProfile(food_preference="vegetarian"),
        week_start=week_start,
    )
    # Use real DB if available; otherwise skip gracefully isn't ideal — mock the SQL path.
    fake_rows = [
        {
            "id": 1,
            "week_start": week_start,
            "day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date.today().weekday()],
            "meal_slot": "lunch",
            "food_description": "Lentil bowl + brown rice + veggies",
            "kcal": 500,
            "protein_g": 22,
            "status": "planned",
            "source_kb_id": "nutrition_everyday_meals",
        }
    ]
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = None
    conn.execute.return_value.fetchall.return_value = fake_rows

    with patch.object(store_mod, "_conn", return_value=conn):
        n = store_mod.replace_diet_plan_week(uid, week_start, meals)
        assert n == len(meals)
        planned = store_mod.diet_meals_for_day(uid, week_start=week_start)
    assert len(planned) == 1
    assert planned[0]["food_description"]
    # INSERT used the authoritative week_start
    insert_calls = [
        c for c in conn.execute.call_args_list if "INSERT INTO diet_plan_days" in str(c)
    ]
    assert insert_calls
    assert insert_calls[0][0][1][1] == week_start


def test_scheduler_overrides_llm_week_start():
    from app.graph.agents import scheduler as sched_mod
    from app.graph.tool_agent import ToolAgentResult

    fake_json = """
Here's a plan.
```json
{
  "week_start": "2025-01-13",
  "days": [
    {"day": "Mon", "focus": "Walk", "duration_min": 30, "status": "planned"},
    {"day": "Wed", "focus": "Strength", "duration_min": 40, "status": "planned"}
  ],
  "calorie_target": 9999,
  "protein_target_g": 1,
  "notes": "placeholder"
}
```
"""
    state = CoachingTeamState(
        profile=UserProfile(
            goal="lose fat",
            sessions_per_week=3,
            preferred_workout_modes=["walking"],
            food_preference="no-preference",
            weight_kg=70,
            height_cm=170,
            age=30,
            sex="female",
            activity_level="moderate",
            onboarding_complete=True,
        ),
        intent="first_plan",
        week_plan=None,
        messages=[{"role": "user", "content": "draft my first week"}],  # type: ignore[list-item]
        user_id="u-week",
    )
    with (
        patch.object(
            sched_mod,
            "run_tool_agent",
            return_value=ToolAgentResult(text=fake_json, tools_called=[], tool_outputs=[]),
        ),
        patch.object(sched_mod, "retrieve_memories", return_value=([], [])),
    ):
        out = sched_mod.scheduler_node(state)
    plan = out["proposals"]["proposed_week_plan"]
    assert plan["week_start"] == current_week_start_iso()
    assert plan["week_start"] != "2025-01-13"
    diet = out["proposals"]["proposed_diet_plan"]
    assert diet
    assert all(m["week_start"] == plan["week_start"] for m in diet)
    # Neutral cuisine (no Indian signal)
    assert diet[0].get("cuisine") == "neutral"

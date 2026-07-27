"""GET /api/food_log/today — meals list + SUM totals (display-only)."""
from datetime import date
from unittest.mock import MagicMock, patch

from app.memory.store import get_daily_totals, today_food_log_snapshot


def test_empty_day_snapshot_zero_totals():
    with (
        patch("app.memory.store.food_logs_for_day", return_value=[]),
        patch("app.memory.store.diet_meals_for_day", return_value=[]),
        patch(
            "app.memory.store.get_daily_totals",
            return_value={
                "date": "2026-07-22",
                "tz": "UTC",
                "kcal_consumed": 0.0,
                "protein_g_consumed": 0.0,
                "carbs_g_consumed": 0.0,
                "fat_g_consumed": 0.0,
                "entry_count": 0,
            },
        ),
    ):
        out = today_food_log_snapshot(
            "u-empty",
            calorie_target=2200,
            protein_target_g=180,
        )
    assert out["meals"] == []
    assert out["planned_meals"] == []
    assert out["totals"]["kcal_consumed"] == 0.0
    assert out["totals"]["entry_count"] == 0
    assert out["targets"]["calorie_target"] == 2200
    assert out["targets"]["protein_target_g"] == 180


def test_totals_match_sql_sum_not_just_row_count():
    """Assert get_daily_totals uses SUM and returns the DB aggregate."""
    fake_row = {
        "kcal_consumed": 1023.0,
        "protein_g_consumed": 49.0,
        "carbs_g_consumed": 120.0,
        "fat_g_consumed": 30.0,
        "entry_count": 2,
    }
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = None
    conn.execute.return_value.fetchone.return_value = fake_row

    with patch("app.memory.store._conn", return_value=conn):
        totals = get_daily_totals("u1", day=date(2026, 7, 22), tz="UTC")

    assert totals["kcal_consumed"] == 1023.0
    assert totals["protein_g_consumed"] == 49.0
    assert totals["entry_count"] == 2
    sql = conn.execute.call_args[0][0]
    assert "SUM(kcal)" in sql
    assert "SUM(protein_g)" in sql


def test_snapshot_meals_and_totals_aligned():
    meals = [
        {
            "id": 1,
            "meal_label": "Lunch",
            "foods": [{"name": "rice"}],
            "kcal": 500.0,
            "protein_g": 20.0,
            "carbs_g": 80.0,
            "fat_g": 10.0,
            "logged_at": "2026-07-22T12:00:00+00:00",
            "source": "photo",
            "notes": None,
        },
        {
            "id": 2,
            "meal_label": None,
            "foods": [{"name": "yogurt"}],
            "kcal": 523.0,
            "protein_g": 29.0,
            "carbs_g": 40.0,
            "fat_g": 20.0,
            "logged_at": "2026-07-22T18:00:00+00:00",
            "source": "text",
            "notes": None,
        },
    ]
    summed = {
        "date": "2026-07-22",
        "tz": "UTC",
        "kcal_consumed": 1023.0,
        "protein_g_consumed": 49.0,
        "carbs_g_consumed": 120.0,
        "fat_g_consumed": 30.0,
        "entry_count": 2,
    }
    planned = [
        {
            "id": 9,
            "day": "Tue",
            "meal_slot": "lunch",
            "food_description": "Dal + rice + paneer",
            "kcal": 580,
            "protein_g": 28,
            "status": "planned",
            "source_kb_id": "nutrition_indian_food_macros",
        }
    ]
    with (
        patch("app.memory.store.food_logs_for_day", return_value=meals),
        patch("app.memory.store.diet_meals_for_day", return_value=planned),
        patch("app.memory.store.get_daily_totals", return_value=summed),
    ):
        out = today_food_log_snapshot("u1", calorie_target=2200, protein_target_g=180)

    assert len(out["meals"]) == 2
    assert out["meals"][0]["meal_label"] == "Lunch"
    assert out["planned_meals"][0]["food_description"] == "Dal + rice + paneer"
    assert out["totals"]["kcal_consumed"] == sum(m["kcal"] for m in meals)
    assert out["totals"]["protein_g_consumed"] == sum(m["protein_g"] for m in meals)


def test_api_handler_empty_day_no_graph_lifespan():
    """Call route handler directly — avoids TestClient lifespan/DB pool."""
    from app.graph.state import WeekPlan
    from app.main import get_food_log_today

    plan = WeekPlan(
        week_start="2026-07-14",
        days=[],
        calorie_target=2200,
        protein_target_g=180,
    )
    with (
        patch("app.main.require_user_id", return_value="demo-veteran"),
        patch("app.main.require_graph", return_value=MagicMock()),
        patch("app.main.week_plan_from_graph", return_value=plan),
        patch(
            "app.main.today_food_log_snapshot",
            return_value={
                "meals": [],
                "totals": {
                    "date": "2026-07-22",
                    "tz": "UTC",
                    "kcal_consumed": 0.0,
                    "protein_g_consumed": 0.0,
                    "carbs_g_consumed": 0.0,
                    "fat_g_consumed": 0.0,
                    "entry_count": 0,
                },
                "targets": {"calorie_target": 2200, "protein_target_g": 180},
            },
        ) as snap,
    ):
        body = get_food_log_today(thread_id=None, tz="UTC", x_user_id="demo-veteran")

    assert body["meals"] == []
    assert body["totals"]["kcal_consumed"] == 0.0
    assert body["totals"]["entry_count"] == 0
    assert body["targets"]["calorie_target"] == 2200
    snap.assert_called_once()
    assert snap.call_args.kwargs["calorie_target"] == 2200
    assert snap.call_args.kwargs["protein_target_g"] == 180

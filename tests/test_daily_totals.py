"""Daily food_log totals for Nutrition remaining-day grounding."""
import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.memory.store import get_daily_totals
from app.tools.agent_tools import NUTRITION_TOOLS, get_today_totals


def test_get_today_totals_in_nutrition_tools():
    names = {getattr(t, "name", None) or getattr(t, "__name__", "") for t in NUTRITION_TOOLS}
    assert "get_today_totals" in names


def test_get_daily_totals_sums_via_sql():
    fake_row = {
        "kcal_consumed": 650.0,
        "protein_g_consumed": 42.0,
        "carbs_g_consumed": 70.0,
        "fat_g_consumed": 18.0,
        "entry_count": 2,
    }
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = None
    cur_result = MagicMock()
    cur_result.fetchone.return_value = fake_row
    conn.execute.return_value = cur_result

    with patch("app.memory.store._conn", return_value=conn):
        out = get_daily_totals("user-1", day=date(2026, 7, 22), tz="UTC")

    assert out["kcal_consumed"] == 650.0
    assert out["protein_g_consumed"] == 42.0
    assert out["entry_count"] == 2
    assert out["date"] == "2026-07-22"
    sql = conn.execute.call_args[0][0]
    assert "SUM(kcal)" in sql
    assert "logged_at >=" in sql
    start, end = conn.execute.call_args[0][1][1], conn.execute.call_args[0][1][2]
    assert start.tzinfo is not None
    assert end - start == timedelta(days=1)


def test_get_today_totals_tool_uses_current_user():
    with (
        patch("app.memory.user_context.get_current_user_id", return_value="u1"),
        patch(
            "app.memory.store.get_daily_totals",
            return_value={
                "date": "2026-07-22",
                "tz": "UTC",
                "kcal_consumed": 100.0,
                "protein_g_consumed": 10.0,
                "carbs_g_consumed": 5.0,
                "fat_g_consumed": 2.0,
                "entry_count": 1,
            },
        ) as mock_totals,
    ):
        raw = get_today_totals.invoke({"tz": "UTC"})
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["kcal_consumed"] == 100.0
    mock_totals.assert_called_once()

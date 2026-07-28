"""Plan week dates: header range and day tiles share one week_start source."""

from __future__ import annotations

from datetime import date, timedelta


def day_of_month_labels(week_start: str) -> list[str]:
    """Mirror of web/lib/plan-dates.ts weekDayOfMonthLabels (Mon=+0 … Sun=+6)."""
    start = date.fromisoformat(week_start)
    return [str((start + timedelta(days=i)).day) for i in range(7)]


def format_week_range(week_start: str) -> tuple[date, date]:
    start = date.fromisoformat(week_start)
    end = start + timedelta(days=6)
    return start, end


def test_known_week_start_jul_27_2026_tiles():
    # Monday Jul 27 → Sun Aug 2, 2026
    labels = day_of_month_labels("2026-07-27")
    assert labels == ["27", "28", "29", "30", "31", "1", "2"]
    assert labels[0] != "01"  # not sequential placeholder index


def test_header_and_tiles_same_source():
    week_start = "2026-07-27"
    start, end = format_week_range(week_start)
    labels = day_of_month_labels(week_start)
    assert start.day == int(labels[0])
    assert end.day == int(labels[-1])
    assert start.month == 7 and end.month == 8
    # Every tile is week_start + offset — not 1..7
    for i, label in enumerate(labels):
        assert int(label) == (start + timedelta(days=i)).day


def test_month_boundary_january():
    labels = day_of_month_labels("2026-01-26")  # Mon Jan 26 → Sun Feb 1
    assert labels == ["26", "27", "28", "29", "30", "31", "1"]
    start, end = format_week_range("2026-01-26")
    assert start.isoformat() == "2026-01-26"
    assert end.isoformat() == "2026-02-01"

"""Unit tests for eval harness helpers (no LLM calls)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))
from helpers import format_summary_table, parse_judge_scores, summarize_results


def test_parse_judge_scores_json():
    raw = '{"groundedness": 4, "plan_sanity": 5, "tone": 4, "safety": 5, "notes": "ok"}'
    scores = parse_judge_scores(raw)
    assert scores["groundedness"] == 4
    assert scores["safety"] == 5


def test_parse_judge_scores_fenced():
    raw = 'Here are scores:\n```json\n{"groundedness": 3, "plan_sanity": 3, "tone": 4, "safety": 4, "notes": "fine"}\n```'
    scores = parse_judge_scores(raw)
    assert scores["plan_sanity"] == 3


def test_summarize_results():
    results = [
        {
            "category": "schedule",
            "judge_scores": {"groundedness": 4, "plan_sanity": 5, "tone": 4, "safety": 5},
        },
        {
            "category": "safety",
            "judge_scores": {"groundedness": 5, "plan_sanity": 4, "tone": 5, "safety": 5},
        },
    ]
    summary = summarize_results(results)
    assert summary["total"] == 2
    assert summary["groundedness"] == 4.5
    assert summary["by_category"]["schedule"]["count"] == 1
    table = format_summary_table(summary)
    assert "Eval summary" in table

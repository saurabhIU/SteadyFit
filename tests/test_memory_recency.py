"""Unit tests for coaching-memory recency weighting (no DB / LLM)."""
from datetime import date, timedelta

from app.graph.citations import citations_from_texts
from app.rag.memory_store import combined_memory_score, recency_weight


def test_recency_weight_decreases_with_age():
    as_of = date(2026, 7, 14)
    fresh = recency_weight(as_of - timedelta(days=7), as_of=as_of, half_life_weeks=8)
    old = recency_weight(as_of - timedelta(days=56), as_of=as_of, half_life_weeks=8)
    assert fresh > old
    assert 0 < old < 1
    # ~8 weeks → ~0.5
    assert abs(old - 0.5) < 0.05


def test_recency_weight_current_week_is_one():
    as_of = date(2026, 7, 14)
    assert recency_weight(as_of, as_of=as_of) == 1.0


def test_combined_score_prefers_recent_when_similarity_close():
    as_of = date(2026, 7, 14)
    recent = as_of - timedelta(days=14)
    ancient = as_of - timedelta(days=180)
    # Slightly better cosine distance for the ancient week
    score_recent = combined_memory_score(0.20, recent, as_of=as_of)
    score_ancient = combined_memory_score(0.15, ancient, as_of=as_of)
    assert score_recent > score_ancient


def test_citations_from_texts_parses_memory_tags():
    cites = citations_from_texts([
        "Short hotel sessions worked. [Memory: week of 2026-06-16] Same approach?"
    ])
    assert len(cites) == 1
    assert cites[0]["kind"] == "memory"
    assert cites[0]["tag"] == "[Memory: week of 2026-06-16]"
    assert cites[0]["source_file"] == "week_2026-06-16"

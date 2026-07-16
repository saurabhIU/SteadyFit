"""Unit tests for hybrid RRF fusion (no LLM / DB)."""
from app.rag.retriever import _rrf_fuse


def _row(doc_id: int, source: str = "x"):
    return (doc_id, source, "text", f"id_{doc_id}", f"{source}.md", {}, 0.1)


def test_rrf_prefers_overlap():
    # Doc 1 ranks high in both → should win over dense-only / sparse-only.
    dense = [_row(1), _row(2), _row(3), _row(4)]
    sparse = [_row(5), _row(1), _row(6), _row(7)]
    fused = _rrf_fuse(dense, sparse, k=3, rrf_k=60)
    assert fused[0][0] == 1


def test_rrf_penalty_for_missing_leg():
    dense = [_row(10), _row(11)]
    sparse = [_row(20)]
    fused = _rrf_fuse(dense, sparse, k=3, rrf_k=60)
    ids = [d for d, _ in fused]
    assert 10 in ids and 11 in ids and 20 in ids
    # Dense #1 should beat sparse-only (penalty on missing dense).
    assert fused[0][0] == 10

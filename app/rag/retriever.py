"""Retrieval over personal docs and curated KB (Postgres + pgvector).

Dense cosine similarity (`retrieve`) plus hybrid dense+FTS RRF (`retrieve_hybrid`).
"""
from __future__ import annotations

from typing import Any

import psycopg
from langchain_openai import OpenAIEmbeddings
from langsmith import traceable
from pgvector import Vector
from pgvector.psycopg import register_vector

from app.config import openai_api_key, settings
from app.rag.ingest import TABLE
from app.security import safe_tool_error, wrap_untrusted
from app.tracing import annotate_run, kb_retriever_outputs, personal_retriever_outputs


def _embed_query(query: str) -> list[float]:
    embedder = OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_api_key)
    return embedder.embed_query(query)


def _citation_from_row(row: Any, *, score: float | None = None) -> dict:
    source, text, kb_id, source_file, meta = row[0], row[1], row[2], row[3], row[4]
    section = ""
    if isinstance(meta, dict):
        section = str(meta.get("section") or "")
    snippet = (text or "")[:280].replace("\n", " ").strip()
    label_src = source_file or source
    cite = {
        "source_file": label_src,
        "section": section,
        "kb_id": kb_id,
        "snippet": snippet,
        "tag": f"[KB: {label_src} — {section}]" if section else f"[KB: {label_src}]",
    }
    if score is not None:
        cite["score"] = round(float(score), 6)
    return cite


def _filter_clauses(
    *,
    doc_types: list[str] | None,
    modality: str | None,
    user_id: str | None,
    kb_shared: bool,
) -> tuple[str, list[Any]]:
    """Shared WHERE builder — applied to both dense and sparse legs."""
    clauses: list[str] = ["TRUE"]
    params: list[Any] = []
    if doc_types:
        clauses.append("doc_type = ANY(%s)")
        params.append(doc_types)
    if modality:
        clauses.append("%s = ANY(modality)")
        params.append(modality)
    if user_id is not None:
        clauses.append("user_id = %s")
        params.append(user_id)
    elif kb_shared:
        # Shared KB corpus: never mix personal chunks in.
        clauses.append("(user_id IS NULL OR doc_type LIKE 'kb_%%')")
    return " AND ".join(clauses), params


@traceable(
    name="retrieve_personal",
    run_type="retriever",
    process_outputs=personal_retriever_outputs,
)
def retrieve_personal(
    query: str,
    k: int = 4,
    collection_filter: str | None = None,
    *,
    user_id: str | None = None,
) -> list[str]:
    """Personal/reference uploads only — never curated KB or other users."""
    from app.memory.user_context import require_current_user_id

    uid = user_id or require_current_user_id()
    annotate_run(inputs={
        "query": query,
        "k": k,
        "user_id": uid,
        "collection_filter": collection_filter,
    })
    try:
        vec = _embed_query(query)
        with psycopg.connect(settings.database_url) as conn:
            register_vector(conn)
            rows = conn.execute(
                f"""
                SELECT source, text, (embedding <=> %s) AS dist FROM {TABLE}
                WHERE user_id = %s
                  AND doc_type IN ('personal', 'program', 'recipes', 'reference', 'knowledge')
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (Vector(vec), uid, Vector(vec), k),
            ).fetchall()
        annotate_run(outputs={
            "n_chunks": len(rows),
            "sources": [
                {"source": r[0], "score": round(float(r[2]), 6)} for r in rows
            ],
        })
        return [
            wrap_untrusted(f"[doc:{source}] {text}", source="doc")
            for source, text, _dist in rows
        ]
    except Exception:
        return [safe_tool_error("doc")]


@traceable(
    name="retrieve_kb",
    run_type="retriever",
    process_outputs=kb_retriever_outputs,
)
def retrieve(
    query: str,
    *,
    doc_types: list[str] | None = None,
    modality: str | None = None,
    k: int = 5,
) -> tuple[list[str], list[dict]]:
    """Filter-then-rank semantic retrieval (dense baseline). Returns (wrapped_chunks, citations)."""
    annotate_run(inputs={
        "query": query,
        "doc_types": doc_types,
        "modality": modality,
        "k": k,
        "mode": "dense",
    })
    try:
        vec = _embed_query(query)
        where, params = _filter_clauses(
            doc_types=doc_types,
            modality=modality,
            user_id=None,
            kb_shared=True,
        )
        params.extend([Vector(vec), Vector(vec), k])
        sql = f"""
            SELECT source, text, kb_id, source_file, meta, (embedding <=> %s) AS dist
            FROM {TABLE}
            WHERE ({where})
            ORDER BY embedding <=> %s
            LIMIT %s
        """
        with psycopg.connect(settings.database_url) as conn:
            register_vector(conn)
            rows = conn.execute(sql, params).fetchall()
        chunks: list[str] = []
        citations: list[dict] = []
        for row in rows:
            dist = float(row[5]) if len(row) > 5 else None
            cite = _citation_from_row(row[:5], score=dist)
            citations.append(cite)
            body = f"{cite['tag']}\n{row[1]}"
            chunks.append(wrap_untrusted(body, source="kb"))
        return chunks, citations
    except Exception:
        return [safe_tool_error("kb")], []


def _rrf_fuse(
    dense_rows: list[tuple],
    sparse_rows: list[tuple],
    *,
    k: int,
    rrf_k: int,
) -> list[tuple[Any, float]]:
    """Reciprocal Rank Fusion over row tuples keyed by documents.id (index 0).

    Rows are (id, source, text, kb_id, source_file, meta, …).
    Missing-leg penalty rank = 2k + 1.
    """
    candidate_n = 2 * k
    penalty = candidate_n + 1
    dense_rank: dict[Any, int] = {}
    sparse_rank: dict[Any, int] = {}
    by_id: dict[Any, tuple] = {}

    for i, row in enumerate(dense_rows):
        doc_id = row[0]
        if doc_id not in dense_rank:
            dense_rank[doc_id] = i + 1
            by_id[doc_id] = row
    for i, row in enumerate(sparse_rows):
        doc_id = row[0]
        if doc_id not in sparse_rank:
            sparse_rank[doc_id] = i + 1
            by_id.setdefault(doc_id, row)

    scored: list[tuple[Any, float]] = []
    for doc_id in by_id:
        score = (
            1.0 / (rrf_k + dense_rank.get(doc_id, penalty))
            + 1.0 / (rrf_k + sparse_rank.get(doc_id, penalty))
        )
        scored.append((doc_id, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


@traceable(
    name="retrieve_hybrid",
    run_type="retriever",
    process_outputs=kb_retriever_outputs,
)
def retrieve_hybrid(
    query: str,
    *,
    doc_types: list[str] | None = None,
    modality: str | None = None,
    user_id: str | None = None,
    k: int = 5,
    rrf_k: int = 60,
) -> tuple[list[str], list[dict]]:
    """Hybrid dense (pgvector) + sparse (Postgres FTS) retrieval with RRF fusion."""
    annotate_run(inputs={
        "query": query,
        "doc_types": doc_types,
        "modality": modality,
        "user_id": user_id,
        "k": k,
        "rrf_k": rrf_k,
        "mode": "hybrid_rrf",
    })
    try:
        candidate_n = max(2 * k, 2)
        vec = _embed_query(query)
        where, base_params = _filter_clauses(
            doc_types=doc_types,
            modality=modality,
            user_id=user_id,
            kb_shared=user_id is None,
        )

        dense_sql = f"""
            SELECT id, source, text, kb_id, source_file, meta, (embedding <=> %s) AS dist
            FROM {TABLE}
            WHERE ({where})
            ORDER BY embedding <=> %s
            LIMIT %s
        """
        sparse_sql = f"""
            SELECT id, source, text, kb_id, source_file, meta,
                   ts_rank(content_tsv, plainto_tsquery('simple', %s)) AS rank
            FROM {TABLE}
            WHERE ({where})
              AND content_tsv @@ plainto_tsquery('simple', %s)
            ORDER BY rank DESC
            LIMIT %s
        """

        with psycopg.connect(settings.database_url) as conn:
            register_vector(conn)
            dense_params = list(base_params) + [Vector(vec), Vector(vec), candidate_n]
            dense_rows = list(conn.execute(dense_sql, dense_params).fetchall())
            sparse_params = list(base_params) + [query, query, candidate_n]
            try:
                sparse_rows = list(conn.execute(sparse_sql, sparse_params).fetchall())
            except Exception:
                # Empty/invalid tsquery or missing FTS column → dense-only fallback.
                sparse_rows = []

        # If FTS found nothing, keep dense order (still return top k).
        if not sparse_rows:
            top = dense_rows[:k]
            fused_scores = {
                row[0]: 1.0 / (rrf_k + i + 1) for i, row in enumerate(top)
            }
        else:
            fused = _rrf_fuse(dense_rows, sparse_rows, k=k, rrf_k=rrf_k)
            by_id = {row[0]: row for row in dense_rows}
            by_id.update({row[0]: row for row in sparse_rows})
            top = [by_id[doc_id] for doc_id, _ in fused if doc_id in by_id]
            fused_scores = {doc_id: score for doc_id, score in fused}

        chunks: list[str] = []
        citations: list[dict] = []
        for row in top:
            # row: id, source, text, kb_id, source_file, meta, …
            cite_row = (row[1], row[2], row[3], row[4], row[5])
            score = fused_scores.get(row[0])
            cite = _citation_from_row(cite_row, score=score)
            citations.append(cite)
            body = f"{cite['tag']}\n{row[2]}"
            chunks.append(wrap_untrusted(body, source="kb"))

        annotate_run(outputs={
            "n_chunks": len(chunks),
            "n_dense": len(dense_rows),
            "n_sparse": len(sparse_rows),
            "sources": [
                {"source_file": c.get("source_file"), "kb_id": c.get("kb_id"),
                 "score": c.get("score")}
                for c in citations
            ],
        })
        return chunks, citations
    except Exception:
        return [safe_tool_error("kb")], []


def retrieve_kb(
    query: str,
    *,
    doc_types: list[str] | None = None,
    modality: str | None = None,
    k: int = 5,
) -> tuple[list[str], list[dict]]:
    """KB path used by agents — hybrid dense+FTS RRF (Task 6)."""
    types = doc_types or ["kb_exercise", "kb_guide", "kb_template", "kb_science"]
    return retrieve_hybrid(query, doc_types=types, modality=modality, k=k)

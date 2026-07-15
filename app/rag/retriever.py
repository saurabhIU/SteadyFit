"""Retrieval over personal docs and curated KB (Postgres + pgvector)."""
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
    """Filter-then-rank semantic retrieval. Returns (wrapped_chunks, citations)."""
    annotate_run(inputs={
        "query": query,
        "doc_types": doc_types,
        "modality": modality,
        "k": k,
    })
    try:
        vec = _embed_query(query)
        clauses = ["TRUE"]
        params: list[Any] = []
        if doc_types:
            clauses.append("doc_type = ANY(%s)")
            params.append(doc_types)
        if modality:
            clauses.append("%s = ANY(modality)")
            params.append(modality)
        where = " AND ".join(clauses)
        # dist for LangSmith metadata only (same ORDER BY key used for ranking)
        params.extend([Vector(vec), Vector(vec), k])
        # Shared KB corpus: never filter by user_id (kb rows keep user_id NULL).
        sql = f"""
            SELECT source, text, kb_id, source_file, meta, (embedding <=> %s) AS dist
            FROM {TABLE}
            WHERE ({where})
              AND (user_id IS NULL OR doc_type LIKE 'kb_%%')
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


def retrieve_kb(
    query: str,
    *,
    doc_types: list[str] | None = None,
    modality: str | None = None,
    k: int = 5,
) -> tuple[list[str], list[dict]]:
    types = doc_types or ["kb_exercise", "kb_guide", "kb_template", "kb_science"]
    return retrieve(query, doc_types=types, modality=modality, k=k)

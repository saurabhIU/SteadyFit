"""Retrieval over personal docs and curated KB (Postgres + pgvector)."""
from __future__ import annotations

from typing import Any

import psycopg
from langchain_openai import OpenAIEmbeddings
from pgvector import Vector
from pgvector.psycopg import register_vector

from app.config import openai_api_key, settings
from app.rag.ingest import TABLE
from app.security import safe_tool_error, wrap_untrusted


def _embed_query(query: str) -> list[float]:
    embedder = OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_api_key)
    return embedder.embed_query(query)


def _citation_from_row(row: Any) -> dict:
    source, text, kb_id, source_file, meta = row[0], row[1], row[2], row[3], row[4]
    section = ""
    if isinstance(meta, dict):
        section = str(meta.get("section") or "")
    snippet = (text or "")[:280].replace("\n", " ").strip()
    label_src = source_file or source
    return {
        "source_file": label_src,
        "section": section,
        "kb_id": kb_id,
        "snippet": snippet,
        "tag": f"[KB: {label_src} — {section}]" if section else f"[KB: {label_src}]",
    }


def retrieve_personal(query: str, k: int = 4, collection_filter: str | None = None) -> list[str]:
    """Personal/reference uploads only — never curated KB doc_types."""
    try:
        vec = _embed_query(query)
        with psycopg.connect(settings.database_url) as conn:
            register_vector(conn)
            rows = conn.execute(
                f"""
                SELECT source, text FROM {TABLE}
                WHERE doc_type IN ('personal', 'program', 'recipes', 'reference', 'knowledge')
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (Vector(vec), k),
            ).fetchall()
        return [
            wrap_untrusted(f"[doc:{source}] {text}", source="doc")
            for source, text in rows
        ]
    except Exception:
        return [safe_tool_error("doc")]


def retrieve(
    query: str,
    *,
    doc_types: list[str] | None = None,
    modality: str | None = None,
    k: int = 5,
) -> tuple[list[str], list[dict]]:
    """Filter-then-rank semantic retrieval. Returns (wrapped_chunks, citations)."""
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
        params.extend([Vector(vec), k])
        sql = f"""
            SELECT source, text, kb_id, source_file, meta
            FROM {TABLE}
            WHERE {where}
            ORDER BY embedding <=> %s
            LIMIT %s
        """
        with psycopg.connect(settings.database_url) as conn:
            register_vector(conn)
            rows = conn.execute(sql, params).fetchall()
        chunks: list[str] = []
        citations: list[dict] = []
        for row in rows:
            cite = _citation_from_row(row)
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

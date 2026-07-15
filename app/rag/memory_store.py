"""Coaching-memory corpus: doc_type='memory' in pgvector."""
from __future__ import annotations

import json
import logging
import math
from datetime import date
from typing import Any

import psycopg
from langchain_openai import OpenAIEmbeddings
from langsmith import traceable
from pgvector import Vector
from pgvector.psycopg import register_vector

from app.config import openai_api_key, settings
from app.memory.weekly_summary import WeeklySummary
from app.rag.ingest import TABLE
from app.security import safe_tool_error, wrap_untrusted
from app.tracing import annotate_run, memory_retriever_outputs

logger = logging.getLogger("steadyfit.memory_store")

DOC_TYPE = "memory"
HALF_LIFE_WEEKS = 8.0


def source_file_for(week_start: date) -> str:
    return f"week_{week_start.isoformat()}"


def recency_weight(
    week_start: date,
    *,
    as_of: date | None = None,
    half_life_weeks: float = HALF_LIFE_WEEKS,
) -> float:
    """Exponential decay: 1.0 for current week, 0.5 after ``half_life_weeks``."""
    as_of = as_of or date.today()
    age_weeks = max(0.0, (as_of - week_start).days / 7.0)
    if half_life_weeks <= 0:
        return 1.0
    return float(0.5 ** (age_weeks / half_life_weeks))


def combined_memory_score(
    cosine_distance: float,
    week_start: date,
    *,
    as_of: date | None = None,
    half_life_weeks: float = HALF_LIFE_WEEKS,
) -> float:
    """Higher is better. Similarity ≈ 1 - cosine_distance, then recency boost."""
    similarity = max(0.0, 1.0 - float(cosine_distance))
    return similarity * recency_weight(
        week_start, as_of=as_of, half_life_weeks=half_life_weeks
    )


def upsert_weekly_memory(summary: WeeklySummary, user_id: str) -> str:
    """Idempotent upsert keyed on (user_id, doc_type, source_file)."""
    if not user_id:
        raise ValueError("user_id is required for coaching memory")
    src = source_file_for(summary.week_start)
    text = summary.to_embed_text().strip()
    if not text:
        raise ValueError("empty memory text")
    embedder = OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_api_key)
    vec = embedder.embed_documents([text])[0]
    meta = {
        "week_start": summary.week_start.isoformat(),
        "context_tags": list(summary.context_tags),
        "section": f"week of {summary.week_start.isoformat()}",
        "kind": "coaching_memory",
        "user_id": user_id,
    }
    with psycopg.connect(settings.database_url) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE} WHERE user_id = %s AND doc_type = %s AND source_file = %s",
                (user_id, DOC_TYPE, src),
            )
            cur.execute(
                f"""
                INSERT INTO {TABLE} (
                    text, source, meta, doc_type, embedding,
                    kb_id, muscle_primary, equipment, modality,
                    difficulty, contraindications, source_file, user_id
                ) VALUES (
                    %s, %s, %s::jsonb, %s, %s,
                    NULL, NULL, NULL, %s,
                    NULL, NULL, %s, %s
                )
                """,
                (
                    text,
                    src,
                    json.dumps(meta),
                    DOC_TYPE,
                    vec,
                    summary.context_tags or None,
                    src,
                    user_id,
                ),
            )
        conn.commit()
    logger.info("upserted memory user=%s %s tags=%s", user_id, src, summary.context_tags)
    return src


def _parse_week_start(meta: Any, source_file: str | None) -> date | None:
    if isinstance(meta, dict) and meta.get("week_start"):
        try:
            return date.fromisoformat(str(meta["week_start"])[:10])
        except ValueError:
            pass
    if source_file and source_file.startswith("week_"):
        try:
            return date.fromisoformat(source_file.removeprefix("week_")[:10])
        except ValueError:
            return None
    return None


def memory_citation(week_start: date, snippet: str = "") -> dict:
    tag = f"[Memory: week of {week_start.isoformat()}]"
    return {
        "source_file": source_file_for(week_start),
        "section": f"week of {week_start.isoformat()}",
        "kb_id": None,
        "snippet": (snippet or "")[:240],
        "tag": tag,
        "kind": "memory",
    }


@traceable(
    name="retrieve_memory",
    run_type="retriever",
    process_outputs=memory_retriever_outputs,
)
def retrieve_memories(
    query: str,
    *,
    user_id: str | None = None,
    k: int = 3,
    fetch_n: int = 12,
    as_of: date | None = None,
    half_life_weeks: float = HALF_LIFE_WEEKS,
) -> tuple[list[str], list[dict]]:
    """Semantic memory retrieval with recency-weighted re-ranking (per user)."""
    from app.memory.user_context import require_current_user_id

    uid = user_id or require_current_user_id()
    annotate_run(inputs={
        "query": query,
        "user_id": uid,
        "k": k,
        "fetch_n": fetch_n,
        "half_life_weeks": half_life_weeks,
    })
    try:
        embedder = OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_api_key)
        vec = embedder.embed_query(query)
        with psycopg.connect(settings.database_url) as conn:
            register_vector(conn)
            rows = conn.execute(
                f"""
                SELECT source, text, source_file, meta, (embedding <=> %s) AS dist
                FROM {TABLE}
                WHERE doc_type = %s AND user_id = %s
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (Vector(vec), DOC_TYPE, uid, Vector(vec), fetch_n),
            ).fetchall()
        ranked: list[tuple[float, Any]] = []
        for row in rows:
            source, text, source_file, meta, dist = row
            ws = _parse_week_start(meta, source_file)
            if ws is None:
                continue
            score = combined_memory_score(
                float(dist), ws, as_of=as_of, half_life_weeks=half_life_weeks
            )
            if math.isnan(score):
                continue
            ranked.append((score, (ws, text, source_file, meta, float(dist))))
        ranked.sort(key=lambda x: x[0], reverse=True)

        chunks: list[str] = []
        citations: list[dict] = []
        header = "This user's relevant past weeks:"
        for score, (ws, text, _sf, _meta, dist) in ranked[:k]:
            cite = memory_citation(ws, snippet=text)
            cite["score"] = round(score, 6)
            cite["distance"] = round(dist, 6)
            cite["source_file"] = _sf
            citations.append(cite)
            body = f"{cite['tag']}\n{text}"
            chunks.append(wrap_untrusted(body, source="memory"))
        if chunks:
            # Prefix once for the agent prompt (not each chunk) — caller may join.
            chunks[0] = f"{header}\n{chunks[0]}"
        return chunks, citations
    except Exception:
        logger.exception("retrieve_memories failed")
        return [safe_tool_error("memory")], []

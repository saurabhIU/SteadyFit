"""Retrieval over the user's personal documents (Postgres + pgvector).
Task 6 upgrade lives here: add BM25/full-text hybrid with RRF."""
import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from langchain_openai import OpenAIEmbeddings
from app.config import settings
from app.rag.ingest import TABLE
from app.security import safe_tool_error, wrap_untrusted


def retrieve_personal(query: str, k: int = 4, collection_filter: str | None = None) -> list[str]:
    try:
        embedder = OpenAIEmbeddings(model="text-embedding-3-small",
                                    api_key=settings.openai_api_key)
        vec = embedder.embed_query(query)
        with psycopg.connect(settings.database_url) as conn:
            register_vector(conn)
            rows = conn.execute(
                f"SELECT source, text FROM {TABLE} "
                f"ORDER BY embedding <=> %s LIMIT %s",
                (Vector(vec), k),
            ).fetchall()
        return [
            wrap_untrusted(f"[doc:{source}] {text}", source="doc")
            for source, text in rows
        ]
    except Exception:
        return [safe_tool_error("doc")]

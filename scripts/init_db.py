"""One-time database initialisation for Postgres (Neon).

Creates the pgvector extension, the shared `documents` table used by both
RAG implementations, an HNSW cosine index, and the LangGraph Postgres
checkpointer schema.

Run:  uv run python scripts/init_db.py
Requires DATABASE_URL in the environment (or .env).
"""
import os
import sys

import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

try:  # pick up .env when run locally
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    """
    CREATE TABLE IF NOT EXISTS documents (
        id BIGSERIAL PRIMARY KEY,
        text TEXT NOT NULL,
        source TEXT NOT NULL,
        meta JSONB NOT NULL DEFAULT '{}'::jsonb,
        doc_type TEXT NOT NULL DEFAULT 'program',
        embedding vector(1536) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    # HNSW: no training-set requirement (unlike ivfflat), fine for a small corpus
    """
    CREATE INDEX IF NOT EXISTS documents_embedding_hnsw
        ON documents USING hnsw (embedding vector_cosine_ops)
    """,
    "CREATE INDEX IF NOT EXISTS documents_source_idx ON documents (source)",
]


def main() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        sys.exit("DATABASE_URL is not set")

    with psycopg.connect(url) as conn:
        for stmt in STATEMENTS:
            conn.execute(stmt)
    print("pgvector extension + documents table + indexes ready")

    # LangGraph checkpointer schema (idempotent; also runs on app startup)
    with psycopg.Connection.connect(
        url, autocommit=True, prepare_threshold=0, row_factory=dict_row
    ) as conn:
        PostgresSaver(conn).setup()
    print("LangGraph checkpointer schema ready")


if __name__ == "__main__":
    main()

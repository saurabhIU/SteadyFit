"""One-time database initialisation for Postgres (Neon).

Creates pgvector, documents (+ user_id), app user/profile/log tables,
indexes, and the LangGraph Postgres checkpointer schema.

Run:  uv run python scripts/init_db.py
Requires DATABASE_URL in the environment (or .env).
"""
import os
import sys
from typing import LiteralString, cast

import psycopg
from psycopg import Connection
from psycopg.rows import DictRow, dict_row
from langgraph.checkpoint.postgres import PostgresSaver

try:
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
        doc_type TEXT NOT NULL DEFAULT 'personal',
        embedding vector(1536) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        kb_id TEXT,
        muscle_primary TEXT[],
        equipment TEXT[],
        modality TEXT[],
        difficulty TEXT,
        contraindications TEXT[],
        source_file TEXT,
        user_id TEXT
    )
    """,
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id TEXT",
    """
    CREATE INDEX IF NOT EXISTS documents_embedding_hnsw
        ON documents USING hnsw (embedding vector_cosine_ops)
    """,
    "CREATE INDEX IF NOT EXISTS documents_source_idx ON documents (source)",
    "CREATE INDEX IF NOT EXISTS documents_doc_type_idx ON documents (doc_type)",
    "CREATE INDEX IF NOT EXISTS documents_user_doc_type_idx ON documents (user_id, doc_type)",
    # Drop pre-multi-user unique index (doc_type, source_file only).
    "DROP INDEX IF EXISTS documents_memory_upsert_uidx",
    """
    CREATE UNIQUE INDEX IF NOT EXISTS documents_memory_user_upsert_uidx
        ON documents (user_id, doc_type, source_file)
        WHERE doc_type = 'memory' AND user_id IS NOT NULL AND source_file IS NOT NULL
    """,
    # Personal uploads are multi-chunk (many rows share user_id/doc_type/source).
    # Idempotent re-ingest is DELETE-by-source then INSERT — not a one-row unique key.
    "DROP INDEX IF EXISTS documents_personal_user_upsert_uidx",
    """
    CREATE INDEX IF NOT EXISTS documents_personal_user_source_idx
        ON documents (user_id, doc_type, source)
        WHERE doc_type IN ('personal','program','recipes','reference','knowledge')
          AND user_id IS NOT NULL
    """,
    # ── multi-profile app state (replaces SQLite) ───────────────────────────
    """
    CREATE TABLE IF NOT EXISTS app_users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY REFERENCES app_users(user_id) ON DELETE CASCADE,
        name TEXT NOT NULL DEFAULT 'athlete',
        goal TEXT NOT NULL DEFAULT '',
        age INTEGER,
        age_declined BOOLEAN NOT NULL DEFAULT FALSE,
        sex TEXT,
        sex_declined BOOLEAN NOT NULL DEFAULT FALSE,
        preferred_workout_modes JSONB NOT NULL DEFAULT '[]'::jsonb,
        food_preference TEXT,
        sessions_per_week INTEGER,
        constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
        constraints_asked BOOLEAN NOT NULL DEFAULT FALSE,
        onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE,
        awaiting_onboarding_confirm BOOLEAN NOT NULL DEFAULT FALSE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS week_plans (
        user_id TEXT NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
        week_start DATE NOT NULL,
        plan JSONB NOT NULL,
        is_current BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (user_id, week_start)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS week_plans_user_current_idx
        ON week_plans (user_id) WHERE is_current
    """,
    """
    CREATE TABLE IF NOT EXISTS workout_log (
        id BIGSERIAL PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
        date DATE NOT NULL,
        focus TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS workout_log_user_date_idx ON workout_log (user_id, date)",
    """
    CREATE TABLE IF NOT EXISTS weight_log (
        id BIGSERIAL PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
        date DATE NOT NULL,
        kg DOUBLE PRECISION NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS weight_log_user_date_idx ON weight_log (user_id, date)",
]


def main() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        sys.exit("DATABASE_URL is not set")

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            for stmt in STATEMENTS:
                cur.execute(cast(LiteralString, stmt))
        conn.commit()
    print("pgvector + documents + app_users/profile/logs ready")

    conn = Connection[DictRow].connect(
        url, autocommit=True, prepare_threshold=0, row_factory=dict_row
    )
    try:
        PostgresSaver(conn).setup()
    finally:
        conn.close()
    print("LangGraph checkpointer schema ready")


if __name__ == "__main__":
    main()

"""Add Postgres full-text search (tsvector + GIN) on documents.text.

Enables the sparse retrieval leg for hybrid BM25-style + dense RRF search.

  uv run python scripts/migrate_add_fts.py

Requires DATABASE_URL. Idempotent. Column is `text` (not `content`).
"""
from __future__ import annotations

import os
import sys
from typing import LiteralString, cast

import psycopg

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

STATEMENTS = [
    # Drop prior english-config column if present so we can recreate with simple.
    "DROP INDEX IF EXISTS documents_content_tsv_idx",
    "ALTER TABLE documents DROP COLUMN IF EXISTS content_tsv",
    # Generated tsvector — simple dictionary preserves IDs/terms without stemming.
    """
    ALTER TABLE documents
      ADD COLUMN content_tsv tsvector
      GENERATED ALWAYS AS (to_tsvector('simple', coalesce(text, ''))) STORED
    """,
    """
    CREATE INDEX IF NOT EXISTS documents_content_tsv_idx
      ON documents USING GIN (content_tsv)
    """,
]


def main() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        sys.exit("DATABASE_URL is not set")
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            for stmt in STATEMENTS:
                cur.execute(cast(LiteralString, stmt))
            # Verify
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'documents' AND column_name = 'content_tsv'
                """
            )
            col = cur.fetchone()
            cur.execute(
                """
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'documents' AND indexname = 'documents_content_tsv_idx'
                """
            )
            idx = cur.fetchone()
            cur.execute(
                "SELECT count(*) FILTER (WHERE content_tsv IS NOT NULL) FROM documents"
            )
            filled = cur.fetchone()
        conn.commit()
    if not col:
        sys.exit("content_tsv column missing after migration")
    if not idx:
        sys.exit("documents_content_tsv_idx missing after migration")
    print(f"FTS ready: content_tsv={col[1]}, index={idx[0]}, rows_with_tsv={filled[0]}")


if __name__ == "__main__":
    main()

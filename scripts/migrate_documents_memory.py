"""Migrate coaching-memory index to multi-user (user_id, doc_type, source_file).

  uv run python scripts/migrate_documents_memory.py

Legacy rows with doc_type='memory' and NULL user_id are tagged demo-veteran so
upserts remain idempotent after the unique index change.
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
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id TEXT",
    "DROP INDEX IF EXISTS documents_memory_upsert_uidx",
    """
    UPDATE documents
    SET user_id = 'demo-veteran'
    WHERE doc_type = 'memory' AND user_id IS NULL
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS documents_memory_user_upsert_uidx
        ON documents (user_id, doc_type, source_file)
        WHERE doc_type = 'memory' AND user_id IS NOT NULL AND source_file IS NOT NULL
    """,
    "CREATE INDEX IF NOT EXISTS documents_doc_type_idx ON documents (doc_type)",
    "CREATE INDEX IF NOT EXISTS documents_user_doc_type_idx ON documents (user_id, doc_type)",
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
    print("documents memory multi-user upsert index ready")


if __name__ == "__main__":
    main()

"""Migrate documents table for curated KB metadata (idempotent, no data drop).

  uv run python scripts/migrate_documents_kb.py
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
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS kb_id TEXT",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS muscle_primary TEXT[]",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS equipment TEXT[]",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS modality TEXT[]",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS difficulty TEXT",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS contraindications TEXT[]",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS source_file TEXT",
    "UPDATE documents SET source_file = source WHERE source_file IS NULL",
    # Normalize older upload types toward personal/reference without wiping
    """
    UPDATE documents SET doc_type = 'personal'
    WHERE doc_type IN ('program', 'recipes') AND COALESCE(kb_id, '') = ''
    """,
    """
    UPDATE documents SET doc_type = 'reference'
    WHERE doc_type = 'knowledge' AND COALESCE(kb_id, '') = ''
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS documents_kb_upsert_uidx
        ON documents (doc_type, kb_id, source_file)
        WHERE kb_id IS NOT NULL
    """,
    "CREATE INDEX IF NOT EXISTS documents_doc_type_idx ON documents (doc_type)",
    """
    CREATE INDEX IF NOT EXISTS documents_muscle_gin
        ON documents USING gin (muscle_primary)
    """,
    """
    CREATE INDEX IF NOT EXISTS documents_equipment_gin
        ON documents USING gin (equipment)
    """,
    """
    CREATE INDEX IF NOT EXISTS documents_modality_gin
        ON documents USING gin (modality)
    """,
    """
    CREATE INDEX IF NOT EXISTS documents_contraindications_gin
        ON documents USING gin (contraindications)
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
        conn.commit()
    print("documents KB columns + GIN indexes ready")


if __name__ == "__main__":
    main()

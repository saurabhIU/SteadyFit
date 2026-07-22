"""Add ephemeral try-profile columns to user_profiles (idempotent).

  uv run python scripts/migrate_ephemeral_profiles.py

Requires DATABASE_URL. Existing rows stay is_ephemeral=false, expires_at=NULL.
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
    """
    ALTER TABLE user_profiles
      ADD COLUMN IF NOT EXISTS is_ephemeral BOOLEAN NOT NULL DEFAULT false
    """,
    """
    ALTER TABLE user_profiles
      ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ NULL
    """,
    """
    CREATE INDEX IF NOT EXISTS user_profiles_ephemeral_expires_idx
      ON user_profiles (expires_at)
      WHERE is_ephemeral = true
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
    print("user_profiles.is_ephemeral + expires_at ready")


if __name__ == "__main__":
    main()

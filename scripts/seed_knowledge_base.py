"""Ingest data/knowledge_base/* into Postgres/pgvector.

Supports .md / .txt / .pdf. Skips README.md. Re-runs are safe: ingest()
replaces chunks per filename.

Requires DATABASE_URL + OPENAI_API_KEY (embeddings).
Run init_db first if the documents table does not exist yet.

  uv run python scripts/init_db.py
  uv run python scripts/seed_knowledge_base.py
"""
from __future__ import annotations

from pathlib import Path

from app.rag.ingest import ingest

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "data" / "knowledge_base"
SUPPORTED = {".md", ".txt", ".markdown", ".pdf"}
SKIP_NAMES = {"readme.md"}


def doc_type_for(path: Path) -> str:
    name = path.name.lower()
    if "recipe" in name:
        return "recipes"
    if "program" in name or name.startswith("sample_my_"):
        return "program"
    # HHS / dietary guidelines PDFs and other curated corpus
    return "knowledge"


def main() -> None:
    if not KB_DIR.is_dir():
        raise SystemExit(f"Knowledge base folder missing: {KB_DIR}")

    files = sorted(
        p for p in KB_DIR.iterdir()
        if p.is_file()
        and p.suffix.lower() in SUPPORTED
        and p.name.lower() not in SKIP_NAMES
    )
    if not files:
        raise SystemExit(f"No .md/.txt/.pdf files to ingest in {KB_DIR}")

    total = 0
    for path in files:
        dtype = doc_type_for(path)
        print(f"Ingesting {path.name}…")
        n = ingest(str(path), doc_type=dtype)
        total += n
        print(f"  → {n} chunks (doc_type={dtype})")

    print(f"Done — {total} chunks from {len(files)} file(s).")


if __name__ == "__main__":
    main()

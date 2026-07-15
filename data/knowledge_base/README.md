# Knowledge base

Curated SteadyFit KB (Volumes 1–7) plus optional personal templates.

```bash
uv run python scripts/init_db.py
uv run python scripts/migrate_documents_kb.py
uv run python -m app.rag.ingest_kb data/knowledge_base/
```

Structured exercise index: `exercise_library.json` (used by `find_exercises` / substitutions — no embeddings).

Personal uploads still go through `POST /api/upload` → `doc_type=personal`.

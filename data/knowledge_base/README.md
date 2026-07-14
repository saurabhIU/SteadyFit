# Knowledge base

Drop curated sources here (Markdown, plain text, or PDF). PDFs are extracted
with pypdf, then chunked the same way as Markdown.

Current guidelines corpus (open HHS docs):

- `Physical_Activity_Guidelines_2nd_edition.pdf`
- `PAG_ExecutiveSummary.pdf`

Plus optional personal templates (`sample_my_program.txt`, etc.).

Seed everything in this folder into pgvector:

```bash
uv run python scripts/init_db.py          # once
uv run python scripts/seed_knowledge_base.py
```

Or upload a single file via the API (backend running):

```bash
curl -F "file=@data/knowledge_base/PAG_ExecutiveSummary.pdf" \
  http://localhost:8000/api/upload
```

# Knowledge base

Author each topic as structured Markdown (H2/H3 sections) — the chunker is
header-aware. Suggested corpus to write/collect (open-licence sources or your
own summaries):

- hypertrophy_programming.md   (volume landmarks, progressive overload, splits)
- nutrition_fundamentals.md    (energy balance, protein targets, cutting)
- recovery_and_sleep.md        (deloads, sleep, training when under-recovered)
- beginner_templates.md        (3-day full body, upper/lower, equipment subs)
- supplements_basics.md        (creatine, protein powder, caffeine)

Upload into the vector store via the API (with the backend running):

```bash
# Markdown sample
curl -F "file=@data/knowledge_base/sample_hypertrophy_basics.md" http://localhost:8000/api/upload

# Plain-text personal program template (edit, then upload via /upload or curl)
curl -F "file=@data/knowledge_base/sample_my_program.txt" http://localhost:8000/api/upload
```

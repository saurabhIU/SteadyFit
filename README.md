# SteadyFit

An agentic AI fitness copilot for everyday people. A LangGraph **AI Coaching Team** —
Coach (supervisor) + Intake, Scheduler, Nutrition, Adherence, Knowledge — grounded in a
**curated knowledge base** (Volumes 1–7 in pgvector), the user's own uploads, **coaching
memory** (past weeks), and live web search (Tavily). Specialists use **LLM tool calling**
(`bind_tools`) for calendar, USDA, exercise lookup, and RAG. Conversational onboarding
fills the profile before coaching; plan changes pause for human approval.

**Multi-profile demo** (no real auth): switch personas with `X-User-Id` /
`?profile=demo-new|demo-veteran`. Profiles, plans, adherence, personal uploads, and
memories are scoped per user in Postgres.

See **PLAN.md** for the full capstone plan (Tasks 1–7).

## Architecture

```
Next.js UI (Vercel) ──► FastAPI API (Render)
  ?profile=…                     X-User-Id header
         │                     │
         │            normalize + scope gate
         │                     │
         │            LangGraph (Postgres checkpointer)
         │            thread = {user_id}:{conversation}
         │                     │
         │              coach (completeness gate)
         │               ├─ intake ──► END | first_plan → scheduler
         │               ├─ scheduler  ┐
         │               ├─ nutrition  ┼─► coaching_team → memory_write
         │               ├─ adherence  │         │
         │               └─ knowledge ─┘         ├─ approve (HITL) | coach loop | END
         │
         └── citations / quick_replies / plan approval cards

External cron ──► POST /internal/weekly-review  (loops every profile)

Tools (agentic): calendar · USDA · Tavily · find_exercises / substitutions · retrieve_*
RAG / memory (all in Postgres + pgvector `documents`):
  personal uploads  ──► ingest.py       ──► doc_type=personal   (user_id required)
  curated KB Volumes──► ingest_kb.py    ──► doc_type=kb_*       (user_id NULL, shared)
  weekly summaries  ──► memory_store.py ──► doc_type=memory     (user_id required)
App state: app_users · user_profiles · week_plans · workout_log · weight_log
Gateway: Vercel AI Gateway · Traces: LangSmith
```

### Turn flow (mermaid)

```mermaid
flowchart TD
  MSG[User message] --> HDR[Resolve X-User-Id]
  HDR --> GATE[Normalize + scope gate]
  GATE -->|out of scope| REFUSE[Fixed fitness redirect]
  GATE -->|in scope| BOOT[bootstrap profile + week plan]
  BOOT --> COACH[Coach]
  COACH -->|onboarding incomplete| INT[Intake: extract → save → ask]
  INT -->|still filling slots| END1[END]
  INT -->|confirmed| SCH1[Scheduler first WeekPlan]
  COACH -->|schedule| SCH[Scheduler + tools + memories]
  COACH -->|nutrition| NUT[Nutrition + tools]
  COACH -->|adherence| ADH[Adherence + tools + memories]
  COACH -->|knowledge| KNOW[Knowledge: personal | KB | web]
  COACH -->|profile change| INT
  SCH --> TEAM[Coaching team merge]
  NUT --> TEAM
  ADH --> TEAM
  KNOW --> TEAM
  SCH1 --> TEAM
  TEAM --> MEM[memory_write\nweekly-review only]
  MEM -->|risk renegotiate| COACH
  MEM -->|plan_changed| HITL[approve interrupt]
  MEM -->|informational| OUT[Reply + citations]
  HITL --> OUT
```

## Quick start

### Backend (API)

```bash
uv sync
cp .env.example .env        # fill in API keys and DATABASE_URL
uv run python scripts/init_db.py
uv run python scripts/migrate_documents_kb.py   # KB metadata columns (idempotent)
uv run python scripts/migrate_documents_memory.py  # multi-user memory upsert index
uv run python -m app.rag.ingest_kb data/knowledge_base/   # curated KB → pgvector
uv run python scripts/seed_memory.py --profile fresh    # demo-new (onboarding)
uv run python scripts/seed_memory.py --profile veteran --no-llm   # demo-veteran (history)
# Add --yes if DATABASE_URL is not localhost (e.g. Neon)
uv run uvicorn app.main:app --reload --port 8000
```

Demo profiles switch in the UI (`?profile=demo-new` / `demo-veteran`); every API call sends `X-User-Id`.

### Frontend (Next.js)

```bash
cd web
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
# open http://localhost:3000  (or /chat?profile=demo-veteran)
```

Personal upload (scoped to the active profile):
```bash
curl -H "X-User-Id: demo-veteran" -F "file=@my_program.md" http://localhost:8000/api/upload
```

Tests and evals:
```bash
uv run pytest tests/
uv run python evals/run_evals.py   # ~53 cases: adversarial, kb_retrieval, onboarding, memory
# Evals use demo-new for onboarding, demo-veteran for everything else
```

**LangSmith (optional):**
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=steadyfit
# Full experiment: uv run python evals/run_evals.py --experiment
```

## Deploy

**API (Render):** `render.yaml` — web service + Sunday cron. Set secrets from `.env.example`.

**Frontend (Vercel):** Root Directory = `web`, set
`NEXT_PUBLIC_API_URL=https://<your-render-api>.onrender.com`.

CORS: `FRONTEND_URL` on Render to your Vercel origin.

## Repo map

```
app/
  main.py / chat_pipeline.py / security.py
  graph/          coach, intake, specialists, coaching_team, memory_write, approve, tool_agent
  rag/            ingest.py (personal) · ingest_kb.py (Volumes) · memory_store.py · retriever.py
  tools/          calendar, food_api, tavily, exercise_lookup, agent_tools (@tool)
  memory/         Postgres profiles + adherence + weekly_summary + user_context
web/              Next.js — chat (chips + citations), plan, update/upload, profile switcher
data/knowledge_base/   Volume1–7 markdown + exercise_library.json
evals/            golden_dataset.jsonl (~53) + harness + LangSmith experiment
scripts/          init_db, migrate_documents_*, seed_memory (--profile fresh|veteran), backfill_memories
tests/            routing, memory isolation, recency weighting
PLAN.md           Capstone Tasks 1–7
```

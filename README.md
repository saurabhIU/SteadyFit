# SteadyFit

An agentic AI fitness copilot for everyday people. A LangGraph **AI Coaching Team** —
Coach (supervisor) + Intake, Scheduler, Nutrition, Adherence, Knowledge — grounded in a
**curated knowledge base** (Volumes 1–7 in pgvector), the user's own uploads, and live web
search (Tavily). Specialists use **LLM tool calling** (`bind_tools`) for calendar, USDA,
exercise lookup, and RAG. Conversational onboarding fills the profile before coaching;
plan changes pause for human approval.

See **PLAN.md** for the full capstone plan (Tasks 1–7).

## Architecture

```
Next.js UI (Vercel) ──► FastAPI API (Render)
         │                     │
         │            normalize + scope gate
         │                     │
         │            LangGraph (Postgres checkpointer)
         │                     │
         │              coach (completeness gate)
         │               ├─ intake ──► END | first_plan → scheduler
         │               ├─ scheduler  ┐
         │               ├─ nutrition  ┼─► coaching_team ─► approve | coach loop | END
         │               ├─ adherence  │
         │               └─ knowledge ─┘
         │
         └── citations / quick_replies / plan approval cards

External cron ──► POST /internal/weekly-review

Tools (agentic): calendar · USDA · Tavily · find_exercises / substitutions · retrieve_*
RAG:
  personal uploads  ──► ingest.py      ──► documents (doc_type=personal)
  curated KB Volumes──► ingest_kb.py   ──► documents (kb_exercise|guide|template|science)
Memory: SQLite profile/adherence · Gateway: Vercel AI Gateway · Traces: LangSmith
```

### Turn flow (mermaid)

```mermaid
flowchart TD
  MSG[User message] --> GATE[Normalize + scope gate]
  GATE -->|out of scope| REFUSE[Fixed fitness redirect]
  GATE -->|in scope| BOOT[bootstrap profile + week plan]
  BOOT --> COACH[Coach]
  COACH -->|onboarding incomplete| INT[Intake: extract → save → ask]
  INT -->|still filling slots| END1[END]
  INT -->|confirmed| SCH1[Scheduler first WeekPlan]
  COACH -->|schedule| SCH[Scheduler + tools]
  COACH -->|nutrition| NUT[Nutrition + tools]
  COACH -->|adherence| ADH[Adherence + tools]
  COACH -->|knowledge| KNOW[Knowledge: personal | KB | web]
  COACH -->|profile change| INT
  SCH --> TEAM[Coaching team merge]
  NUT --> TEAM
  ADH --> TEAM
  KNOW --> TEAM
  SCH1 --> TEAM
  TEAM -->|risk renegotiate| COACH
  TEAM -->|plan_changed| HITL[approve interrupt]
  TEAM -->|informational| OUT[Reply + citations]
  HITL --> OUT
```

## Quick start

### Backend (API)

```bash
uv sync
cp .env.example .env        # fill in API keys and DATABASE_URL
uv run python scripts/init_db.py
uv run python scripts/migrate_documents_kb.py   # KB metadata columns (idempotent)
uv run python -m app.rag.ingest_kb data/knowledge_base/   # curated KB → pgvector
uv run python scripts/seed_memory.py            # complete demo profile
# uv run python scripts/seed_memory.py --fresh  # empty profile → intake demo
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend (Next.js)

```bash
cd web
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
# open http://localhost:3000
```

Personal upload (stays separate from shared KB):
```bash
curl -F "file=@my_program.md" http://localhost:8000/api/upload
```

Tests and evals:
```bash
uv run pytest tests/
uv run python evals/run_evals.py   # golden set incl. adversarial + kb_retrieval + onboarding
```

**LangSmith (optional):**
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=steadyfit
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
  graph/          coach, intake, specialists, coaching_team, approve, tool_agent
  rag/            ingest.py (personal) · ingest_kb.py (Volumes) · retriever.py
  tools/          calendar, food_api, tavily, exercise_lookup, agent_tools (@tool)
  memory/         SQLite profile + adherence
web/              Next.js — chat (chips + citations), plan, update/upload
data/knowledge_base/   Volume1–7 markdown + exercise_library.json
evals/            golden_dataset.jsonl + harness
scripts/          init_db, migrate_documents_kb, seed_memory, seed_knowledge_base
tests/
PLAN.md           Capstone Tasks 1–7
```

# OneRepMax

An agentic AI fitness copilot for everyday people. A LangGraph "coaching council" —
Coach (supervisor), Scheduler, Nutrition, Adherence — grounded in your own uploaded
fitness documents (Agentic RAG via pgvector on Postgres/Neon) and live web search (Tavily), that
autonomously re-plans your training and nutrition week around real life.

See **PLAN.md** for the full capstone plan (Tasks 1–7 deliverables).

## Architecture

```
Next.js UI (Vercel) ──► FastAPI API (Render)
                              │
                    LangGraph state graph
                     coach ──► {scheduler | nutrition | adherence | knowledge}
                              │
                           council
                              │
                    approve (human-in-the-loop interrupt) ──► END

External cron ──► POST /internal/weekly-review (Sunday review)
Tools: Tavily · USDA FoodData · Calendar (mock)
RAG:   uploads ──► chunk ──► embed ──► Postgres (pgvector)
Memory: Postgres checkpointer + SQLite profile/adherence store
Gateway: Vercel AI Gateway · Monitoring: LangSmith
```

## Quick start

### Backend (API)

```bash
uv sync
cp .env.example .env        # fill in API keys and DATABASE_URL
uv run python scripts/init_db.py   # once: pgvector + checkpointer schema
uv run python scripts/seed_memory.py   # optional: demo profile + week plan + workout logs
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

Upload a document (your program / recipes):
```bash
curl -F "file=@my_program.md" http://localhost:8000/api/upload
```

Run tests and evals:
```bash
uv run pytest tests/
uv run python evals/run_evals.py   # 20-case harness; writes evals/summary.md
```

**LangSmith tracing (optional, recommended for demo):**
```bash
# in .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=onerepmax
```

## Deploy

**API (Render):** Push to GitHub, connect the repo — `render.yaml` defines a web service
(FastAPI via uv) and a weekly cron job. Set secrets in the Render dashboard (same as `.env.example`).

**Frontend (Vercel):** Import the repo, set **Root Directory** to `web`, add:
`NEXT_PUBLIC_API_URL=https://<your-render-api>.onrender.com`

Then set `FRONTEND_URL=https://<your-vercel-app>.vercel.app` on Render for CORS.

## Repo map

```
app/                 FastAPI backend (uvicorn app.main:app)
web/                 Next.js frontend (Vercel)
  app/chat/          Coaching chat UI
  app/plan/          Weekly plan + adherence view
  components/        Header, ChatView, PlanView, CouncilPanel
  lib/               Typed API client
evals/               golden dataset + LLM-as-judge harness
tests/               routing smoke tests (no LLM calls)
```

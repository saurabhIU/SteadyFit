# OneRepMax — Agent Context

Multi-agent LangGraph fitness coaching copilot (capstone scaffold). A **Coach supervisor** routes user messages to specialist agents, merges their proposals in a **council** step, optionally **renegotiates** when adherence risk conflicts with plan density, and pauses for **human-in-the-loop approval** before persisting plan changes.

Full product/architecture rationale: **PLAN.md**. Quick start and deploy: **README.md**.

---

## What this app does

OneRepMax helps busy adults stay consistent by **adaptive re-planning** — rescheduling workouts around calendar conflicts, adjusting nutrition after real meals, flagging drop-off risk, and grounding answers in the user's **uploaded documents** (Agentic RAG) or **live web search** (Tavily).

Every turn (user chat or Sunday weekly-review cron) enters at the Coach, loads profile/adherence context, routes to specialists, synthesizes a reply, and checkpoints state in Postgres.

---

## LangGraph supervisor pattern

### Graph topology (`app/graph/build.py`)

```
entry → coach (supervisor: classify intent)
          ├─ schedule   → scheduler
          ├─ nutrition  → nutrition
          ├─ adherence  → adherence
          └─ knowledge  → knowledge (agentic RAG)
specialists → council (Coach merges proposals)
council → coach      (if risk_flag && council_rounds < MAX; renegotiate / simplify)
council → approve    (if proposals.plan_changed; LangGraph interrupt)
council → END        (informational answer)
approve → END
```

**Conditional edges:**
- `route_from_coach`: reads `state.intent` → specialist node name
- `route_from_council`: `risk_flag` loops back to Coach (max 2 rounds); `plan_changed` → HITL interrupt; else END

**Human-in-the-loop:** `approve_node` in `app/graph/supervisor.py` calls `langgraph.types.interrupt()` with the proposed plan. The API resumes with `Command(resume=...)`.

**Checkpointer:** Postgres via `langgraph.checkpoint.postgres.PostgresSaver` (Neon in prod, local Postgres in dev). Schema created by `scripts/init_db.py` and idempotently on startup in `build_graph()`.

---

## CouncilState schema (`app/graph/state.py`)

Shared Pydantic state every `app/` agent node reads/writes:

| Field | Type | Owner / purpose |
|---|---|---|
| `messages` | `Annotated[list, add_messages]` | Conversation history (LangGraph reducer) |
| `profile` | `UserProfile` | Long-term user context (goal, injuries, prefs) |
| `week_plan` | `Optional[WeekPlan]` | Current weekly training + macro targets |
| `intent` | `Optional[str]` | Coach sets: `schedule` \| `nutrition` \| `adherence` \| `knowledge` |
| `proposals` | `dict` | Specialist name → proposal text/JSON; may include `plan_changed: True` |
| `risk_flag` | `bool` | Adherence agent: drop-off risk → council loops to Coach |
| `council_rounds` | `int` | Loop guard (incremented in `coach_node`) |
| `retrieved_context` | `list[str]` | RAG chunks / Tavily results with `[doc:…]` / `[web:…]` source tags |

**Nested models:**
- `UserProfile`: name, goal, sessions_per_week, injuries, food_preferences
- `WeekPlan`: week_start, days (`WorkoutDay[]`), calorie_target, protein_target_g, notes
- `WorkoutDay`: day, focus, duration_min, status (`planned` \| `done` \| `skipped` \| `moved`)

---

## Agent responsibilities

| Agent | File | Intent trigger | Tools / data | Output |
|---|---|---|---|---|
| **Coach** (supervisor) | `app/graph/supervisor.py` | entry + renegotiation loop | LLM intent classification | Sets `intent`; council merges final reply |
| **Scheduler** | `app/graph/agents/scheduler.py` | `schedule` | `calendar_tool` (mock JSON → Google Calendar stretch) | Re-planned week proposal; sets `plan_changed` |
| **Nutrition** | `app/graph/agents/nutrition.py` | `nutrition` | RAG (recipes), `food_api` (USDA) | Macro adjustments, non-judgmental guidance |
| **Adherence** | `app/graph/agents/adherence.py` | `adherence` | `memory/store` (SQLite adherence stats) | Drop-off check-in; sets `risk_flag` if reply starts with `RISK` |
| **Knowledge** | `app/graph/agents/knowledge.py` | `knowledge` | Agentic RAG router → personal pgvector **or** Tavily **or** both | Populates `retrieved_context` |

**Agentic RAG routing** (`knowledge_node`): LLM chooses `personal` \| `web` \| `both` before retrieval — not blind RAG on every question.

**Council** (`council_node`): Merges specialist proposals + retrieved context into one user-facing reply. If adherence risk and plan got harder, conditional edge sends flow back to Coach to simplify.

---

## Infrastructure & tools

| Concern | Implementation |
|---|---|
| LLM gateway | Vercel AI Gateway (`app/config.py` → `get_llm()`); primary `anthropic/claude-sonnet-4.5`, judge `openai/gpt-4o-mini` |
| Embeddings | OpenAI `text-embedding-3-small` (direct OpenAI key, not the gateway) |
| Vector store | Postgres + pgvector (`documents` table); was Qdrant in PLAN.md — **code uses pgvector** |
| Short-term memory | LangGraph Postgres checkpointer (thread_id per chat / weekly-review) |
| Long-term memory | SQLite `data/profile.sqlite` — workout_log, weight_log, profile (`app/memory/store.py`) |
| Web search | Tavily (`app/tools/tavily_search.py`) — degrades with `[web:error]` |
| Nutrition API | USDA FoodData Central (`app/tools/food_api.py`) |
| Calendar | Mock JSON `data/mock_calendar.json` (`app/tools/calendar_tool.py`) |
| Monitoring | LangSmith via `LANGCHAIN_*` env vars (optional) |
| Weekly review | External cron → `POST /internal/weekly-review` with `X-Internal-Secret` (Render cron in `render.yaml`) |

---

## File layout

```
app/                          # Primary runtime (README quick start: uvicorn app.main:app)
  main.py                     # FastAPI: /api/chat, /api/upload, /health, /internal/weekly-review
  config.py                   # Settings + Vercel AI Gateway LLM factory
  graph/
    state.py                  # CouncilState, UserProfile, WeekPlan
    build.py                    # StateGraph wiring + Postgres checkpointer
    supervisor.py             # coach_node, council_node, approve_node
    agents/
      scheduler.py
      nutrition.py
      adherence.py
      knowledge.py
  rag/
    ingest.py                 # Markdown-aware chunking → embed → pgvector
    retriever.py              # Cosine similarity search (Task 6: hybrid BM25+RRF planned)
  tools/
    tavily_search.py
    food_api.py
    calendar_tool.py
  memory/
    store.py                  # SQLite profile + adherence stats
    context.py                # Bootstrap graph state; persist approved plans

web/                          # Next.js frontend (Vercel deploy; Root Directory = web)
  app/chat/                   # Coaching chat page
  app/plan/                   # Weekly plan + adherence view
  app/upload/                 # Document upload for RAG
  components/                 # ChatView, CouncilPanel, PlanApprovalCard, Header, ai-elements
  lib/api.ts                  # Typed client → NEXT_PUBLIC_API_URL (chat + approve)

scripts/init_db.py            # pgvector extension, documents table, checkpointer schema
scripts/seed_memory.py        # Demo profile, week plan, workout logs (SQLite)
evals/                        # golden_dataset.jsonl (20 cases), run_evals.py, summary.md output
tests/test_graph.py           # Routing smoke tests (no LLM calls)
tests/test_evals.py           # Eval helper unit tests
data/                         # Runtime: uploads/, profile.sqlite, mock_calendar.json, knowledge_base/
PLAN.md                       # Capstone Tasks 1–7 (architecture diagrams, eval plan)
render.yaml                   # Render web service + Sunday cron
pyproject.toml                # uv project; ships `app` package
```

---

## API surface (`app/main.py`)

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check (Render + Vercel smoke tests) |
| `POST /api/chat` | `{message, thread_id?}` → invoke graph; returns `reply`, `council`, optional `pending_approval` |
| `POST /api/approve` | `{thread_id, decision: accept\|reject}` → resume HITL interrupt; returns same shape as chat |
| `GET /api/plan` | `?thread_id=` → profile, `week_plan`, adherence stats (checkpoint + SQLite fallback) |
| `GET /api/chat/history` | `?thread_id=` → restored messages + pending approval |
| `POST /api/upload` | Ingest user doc (program/recipes) into pgvector |
| `POST /internal/weekly-review` | Autonomous Sunday review (cron + shared secret) |

---

## Local development

```bash
uv sync
cp .env.example .env
uv run python scripts/init_db.py
uv run uvicorn app.main:app --reload --port 8000

# separate terminal
cd web && cp .env.local.example .env.local && npm install && npm run dev
# http://localhost:3000
```

**Required env vars for basic chat:** `AI_GATEWAY_API_KEY`, `DATABASE_URL`  
**Required for RAG/uploads:** `OPENAI_API_KEY` (embeddings)  
**Optional (graceful degradation):** `TAVILY_API_KEY`, `USDA_API_KEY`, `LANGCHAIN_*`  
**Production cron:** `INTERNAL_CRON_SECRET`, `FRONTEND_URL` (CORS)

Do not commit `.env`. See `.env.example` for the full checklist.

---

## Conventions for contributors

- **Tone:** Warm, concrete, never guilt-tripping — everyday people, not pro athletes.
- **Grounding:** Cite sources via `[doc:…]` / `[web:…]` tags in retrieved context.
- **Plan changes:** Always go through the `approve` interrupt before persisting.
- **Chunking:** Structure-aware (~750 tokens / 3000 chars, 100-token overlap) in `app/rag/ingest.py`; split on markdown headers first to keep whole workout days/recipes.
- **Tests:** `uv run pytest tests/` — routing only, no live LLM.
- **Evals:** `uv run python evals/run_evals.py`
- **Package manager:** `uv` (not pip directly). Python ≥ 3.12.

---

## Build status (scaffold)

Per PLAN.md Task 4–5, remaining work may include: hybrid retrieval (Task 6), council critique loop, Loom demo. **Phase 1** (upload UI, plan refresh, workout prefs) and **Phase 2** (20-case eval harness + RAGAS) are wired. Check git history and PLAN.md checklist for current completion state.

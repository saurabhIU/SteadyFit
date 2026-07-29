# SteadyFit — Agent Context

Multi-agent LangGraph fitness coaching copilot. A **Coach supervisor** routes user
messages (or Sunday weekly-review cron) to specialist agents, runs a **critique**
pass on plan-changing drafts, merges proposals in **coaching_team**, optionally
**renegotiates** when adherence risk conflicts with plan density, writes weekly
**coaching memory**, and pauses for **HITL approval** before persisting plan changes.

Full product/architecture rationale: **deliverables.md**. Changelog + eval pointers:
**IMPROVEMENTS_LOG.md**. Quick start and deploy: **README.md**.

---

## What this app does

SteadyFit helps busy adults stay consistent by **adaptive re-planning** —
rescheduling workouts around calendar conflicts, adjusting nutrition after real
meals (including photo logs), flagging drop-off risk, building a first week of
**workouts + KB meals** after a diet-metrics gate, and grounding answers in the
user's **uploaded documents**, a curated **KB** (hybrid dense+FTS RRF),
**coaching memory**, or **live web search** (Tavily).

Every turn enters at the Coach, loads profile/adherence context, routes to
specialists, synthesizes a reply, and checkpoints state in Postgres.

---

## LangGraph supervisor pattern

### Graph topology (`app/graph/build.py`)

```
entry → coach (supervisor: classify intent + gates)
          ├─ intake     → (still asking → END) | first_plan → scheduler
          ├─ schedule   → scheduler
          ├─ nutrition  → nutrition
          ├─ adherence  → adherence
          └─ knowledge  → knowledge (agentic RAG)
specialists → critique (plan-changing only; ≤1 revise back to specialist)
            → coaching_team → memory_write
memory_write → coach   (if risk_flag && rounds < MAX; renegotiate / simplify)
memory_write → approve (if proposals.plan_changed; LangGraph interrupt)
memory_write → END     (informational answer)
approve → END
```

**Conditional edges:**
- `route_from_coach`: reads `state.intent` → specialist / intake
- `route_after_specialist` / `route_from_critique`: critique or skip → coaching_team
- `route_from_coaching_team` (on `memory_write`): risk loop → coach; `plan_changed` → approve; else END

**Human-in-the-loop:** `approve_node` in `app/graph/supervisor.py` calls
`langgraph.types.interrupt()` with the proposed plan (+ diet/macros when present).
The API resumes with `Command(resume=...)`.

**Checkpointer:** Postgres via `langgraph.checkpoint.postgres.PostgresSaver`
(Neon in prod). Schema via `scripts/init_db.py` and on startup in `build_graph()`.

### Deterministic helpers (not LLM)

| Module | Role |
|---|---|
| `plan_utils.py` | `resolve_relative_day`, `calendar_truth_block`, informational day-plan reply |
| `plan_diff.py` | Diff prior vs proposed week → concrete `plan_changed` chat body |
| `condition_food.py` | Diabetes / hypertension nudges on meal-log-only path |
| `tdee.py` / `diet_gate.py` / `diet_plan.py` | Metrics gate + Mifflin–St Jeor + KB meal week |
| `personalization.py` | Code-level personal-doc RAG injected into scheduler/nutrition prompts |

Relative-day asks (`today` / `tomorrow`) are routed to `schedule` with calendar
truth — never LLM weekday inference. Critique skips `relative_day_info`,
meal-log-only, and micro-session turns.

---

## CoachingTeamState schema (`app/graph/state.py`)

Shared Pydantic state every agent node reads/writes (name may still appear as
CouncilState in older notes — **code uses CoachingTeamState**):

| Field | Type | Owner / purpose |
|---|---|---|
| `messages` | `Annotated[list, add_messages]` | Conversation history (LangGraph reducer) |
| `profile` | `UserProfile` | Long-term user context (goal, injuries, prefs, diet metrics) |
| `week_plan` | `Optional[WeekPlan]` | Current weekly training + macro targets |
| `intent` | `Optional[str]` | Coach sets: `schedule` \| `nutrition` \| `adherence` \| `knowledge` \| `intake` \| … |
| `proposals` | `dict` | Specialist name → proposal; may include `plan_changed`, `relative_day_info` |
| `risk_flag` | `bool` | Adherence: drop-off risk → loop to Coach |
| `coaching_team_rounds` | `int` | Loop guard |
| `retrieved_context` | `list[str]` | RAG / Tavily / Memory chunks with source tags |

**Nested models:** `UserProfile`, `WeekPlan`, `WorkoutDay` (status:
`planned` \| `done` \| `skipped` \| `moved`), plus diet-plan / food-log shapes
in memory store.

---

## Agent responsibilities

| Agent | File | Intent trigger | Tools / data | Output |
|---|---|---|---|---|
| **Coach** | `supervisor.py` | entry + renegotiation | LLM intent + gates | Sets `intent`; relative-day → schedule |
| **Intake** | `agents/intake.py` | incomplete profile / diet gate | extract + persist slots | One question or handoff to first_plan |
| **Scheduler** | `agents/scheduler.py` | `schedule` / first_plan | calendar, exercise_lookup, TDEE, personalization, calendar_truth | Week proposal; `plan_changed` or info day reply |
| **Nutrition** | `agents/nutrition.py` | `nutrition` / photo | USDA, meal vision, totals, condition_food | Macros, meal log, nudges |
| **Adherence** | `agents/adherence.py` | `adherence` | workout/weight logs, memory | Check-in; may set `risk_flag` |
| **Knowledge** | `agents/knowledge.py` | `knowledge` | Agentic RAG: personal \| web \| both + KB | `retrieved_context` |
| **Critique** | `critique.py` | after specialists | rules (knee / prefs / volume) | Pass or revise ≤1 |
| **Coaching team** | `supervisor.py` | after critique | merge + **plan_diff** for plan_changed | Final user reply |
| **Memory write** | `agents/memory_write.py` | weekly-review turns | pgvector `doc_type=memory` | Upsert weekly summary |

**Agentic RAG routing** (`knowledge_node`): LLM chooses `personal` \| `web` \|
`both` before retrieval — not blind RAG on every question.

---

## Infrastructure & tools

| Concern | Implementation |
|---|---|
| LLM gateway | Vercel AI Gateway (`app/config.py` → `get_llm()`); primary `anthropic/claude-sonnet-4.5`, judge `openai/gpt-4o-mini` |
| Embeddings | OpenAI `text-embedding-3-small` (direct OpenAI key) |
| Vector store | Postgres + pgvector (`documents`: personal / `kb_*` / memory) |
| Short-term memory | LangGraph Postgres checkpointer (`thread = {user_id}:{conversation}`) |
| Long-term memory | Postgres profiles / week_plans / diet_plan_days / food_log / workout_log (`app/memory/store.py`); header `X-User-Id` |
| Ephemeral guests | `try-*` profiles, **4h TTL**, cleanup cron |
| Web search | Tavily — degrades with `[web:error]` |
| Nutrition API | USDA FoodData Central |
| Calendar | Mock JSON `data/mock_calendar.json` |
| Monitoring | LangSmith via `LANGCHAIN_*` (optional); see `TRACING.md` |
| Weekly review | Cron → `POST /internal/weekly-review` + `X-Internal-Secret` |

---

## File layout

```
app/
  main.py / chat_pipeline.py / security.py
  config.py
  graph/
    state.py · build.py · supervisor.py · critique.py
    plan_utils.py · plan_diff.py · condition_food.py
    diet_gate.py · tdee.py · diet_plan.py · personalization.py
    tool_agent.py · agents/{scheduler,nutrition,adherence,knowledge,intake,memory_write}
  rag/     ingest · ingest_kb · memory_store · retriever (hybrid RRF)
  tools/   calendar · food_api · tavily · exercise_lookup · meal_vision · agent_tools
  memory/  store.py · context.py
web/       chat · plan · upload · ProfileSwitcher
scripts/   init_db · seed_memory · migrate_*
evals/     golden_dataset.jsonl (120) · run_evals.py · summaries
tests/     routing + plan_diff + relative_day + …
data/      knowledge_base/ · eval_uploads/ · mock_calendar.json
```

---

## API surface (`app/main.py`)

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health check |
| `POST /api/chat` | Invoke graph; `reply`, council transcript, optional `pending_approval` |
| `POST /api/approve` | Resume HITL (`accept` \| `reject`) |
| `GET /api/plan` | Profile, week_plan, diet, adherence |
| `GET /api/chat/history` | Restored messages + pending approval |
| `GET /api/food_log/today` | Daily macro totals |
| `POST /api/upload` | Ingest personal doc into pgvector |
| `POST /api/profiles/try` | Create ephemeral `try-*` guest |
| `POST /internal/weekly-review` | Autonomous Sunday review |
| `POST /internal/cleanup-expired-profiles` | Expire `try-*` guests |

---

## Local development

```bash
uv sync
cp .env.example .env
uv run python scripts/init_db.py
uv run uvicorn app.main:app --reload --port 8000

# separate terminal
cd web && cp .env.local.example .env.local && npm install && npm run dev
# http://localhost:3000  ·  /chat?profile=demo-veteran  ·  Try it yourself
```

**Required:** `AI_GATEWAY_API_KEY`, `DATABASE_URL`  
**RAG/uploads:** `OPENAI_API_KEY`  
**Optional:** `TAVILY_API_KEY`, `USDA_API_KEY`, `LANGCHAIN_*`  
**Prod cron:** `INTERNAL_CRON_SECRET`, `FRONTEND_URL`

Do not commit `.env`. See `.env.example`.

---

## Conventions for contributors

- **Tone:** Warm, concrete, never guilt-tripping.
- **Grounding:** Cite `[KB:…]` / `[Memory:…]` / `[doc:…]` / `[web:…]`.
- **Plan changes:** Always through the `approve` interrupt before persisting.
- **Calendar / diffs:** Prefer `plan_utils` / `plan_diff` over LLM weekday or vague merge copy.
- **Tests:** `uv run pytest tests/` — no live LLM in unit/routing tests.
- **Evals:** `uv run python evals/run_evals.py` (120 golden cases).
- **Package manager:** `uv`. Python ≥ 3.12.

---

## Build status

Hybrid retrieval, council critique, photo meal log, try-yourself, diet gate +
TDEE + diet week, relative-day + plan_diff, and condition-food nudges are
shipped. Remaining Demo Day item: Loom video. See **deliverables.md** Task 7
checklist and **IMPROVEMENTS_LOG.md**.

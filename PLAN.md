# SteadyFit — Capstone Plan & Architecture

An agentic AI fitness copilot for everyday people, built as a multi-agent LangGraph system
with Agentic RAG over the user's own fitness data.

---

## Task 1: Defining Problem, Audience, and Scope

### Problem (one sentence, no solution implied)

Busy working adults who want to get fit consistently fall off their workout and nutrition
plans within weeks because everyday life — meetings, travel, fatigue, and social meals —
keeps breaking plans that never adapt.

### Why this is a problem (who, what, today, why it fails)

The user is a **busy working professional (25–45)** — think a software engineer, analyst, or
manager — who has joined a gym, wants to lose fat or build muscle, and can realistically
train 3–4 times a week. Their "job function" being automated here is the unpaid second job
of **self-coaching**: planning workouts, planning meals, tracking food, and re-planning every
time life interferes.

Today they cobble together a static plan from a YouTube program or a PDF, a workout logger
(Hevy/Strong), a calorie tracker (MyFitnessPal), and a calendar. None of these talk to each
other, and none of them act on their own. When Tuesday's workout is killed by a late meeting,
nothing reschedules it. When they eat out three times in a week, nothing rebalances the
remaining days. When they silently skip two weeks, nothing notices, simplifies the plan, or
checks in. The tools are passive trackers; all of the adaptive decision-making — the part
people are worst at when tired and demotivated — is left to the user. The predictable result
is the industry's well-known drop-off curve: most gym-goers quit within a few months, not
because their plan was wrong, but because nothing helped the plan survive contact with
real life.

### Current-state workflow diagram

```mermaid
flowchart TD
    A[User picks a static plan\nYouTube / PDF / trainer template] --> B[Manually schedules workouts\nin calendar app]
    B --> C[Trains and logs sets\nin Hevy / Strong]
    C --> D[Logs food manually\nin MyFitnessPal]
    D --> E{Life interferes?\nmeeting / travel / fatigue}
    E -- yes --> F[Workout silently skipped\n-- nothing reschedules]
    F --> G[User manually re-plans week\n-- slow, often skipped]
    G --> H{Motivation check}
    E -- no --> C
    H -- low --> I[Gradual drop-off\n-- no one notices]
    H -- ok --> C

    style F fill:#fdd
    style G fill:#fdd
    style I fill:#fdd
```

Pain points (red): the re-planning step is manual and usually skipped; missed sessions are
invisible; drop-off is only discovered after it has already happened.

### Evaluation questions / input–output pairs (seed set)

| # | Input (user message / event) | Expected output behavior |
|---|---|---|
| 1 | "I missed Monday's leg day and I'm traveling Wed–Fri with only a hotel gym." | Redistributed week: leg session moved, hotel-gym-friendly substitutions (dumbbell/machine), no guilt language. |
| 2 | "I had biryani and a mango lassi at a work lunch." | Reasonable calorie/macro estimate logged; remaining-day guidance adjusted; no shaming. |
| 3 | "What does my own program say I should do for a deload week?" | Answer grounded in the **user's uploaded program PDF** (RAG citation), not generic advice. |
| 4 | "Is creatine safe to take daily?" | Web-search-grounded answer (Tavily) with sources; safe, evidence-based framing. |
| 5 | Sunday review trigger (no user input) | Autonomous weekly summary: adherence %, weight trend, next week's plan proposal, one-tap approval request. |
| 6 | User has skipped 3 sessions in 10 days | Adherence agent flags risk; plan is **simplified** (fewer/shorter sessions), supportive check-in sent. |
| 7 | "Give me a high-protein dinner from my recipes under 600 kcal." | Recipe retrieved from user's uploaded recipe collection (RAG), macros verified via food API. |
| 8 | "Should I bulk or cut?" | Asks for/uses profile data (weight trend, goal, body-fat estimate); reasoned recommendation, not generic. |

---

## Task 2: Propose a Solution

### Solution (one sentence)

SteadyFit is a proactive multi-agent fitness copilot — a LangGraph "coaching council" of
Coach, Scheduler, Nutrition, and Adherence agents — that grounds its advice in the user's own
uploaded fitness documents (Agentic RAG) and live web search, and autonomously re-plans the
user's training and nutrition week around their real life.

### Infrastructure diagram

```mermaid
flowchart TD
    U[Browser UI\nphone + laptop] --> FE[Next.js frontend\nchat + plan + upload\nVercel]
    FE --> API[FastAPI backend\nRender]
    CRON[Render cron job\nSunday weekly review] --> API
    API --> LG[LangGraph state graph]
    LG --> GW[Vercel AI Gateway\nClaude Sonnet / GPT-4o-mini]
    LG --> RET[Retriever]
    RET --> PG[(Postgres + pgvector\nNeon: documents + checkpointer)]
    ING[Ingestion pipeline\nchunk + embed] --> PG
    UP[User uploads\nprogram PDFs, recipes, logs] --> ING
    LG --> TAV[Tavily\nweb search tool]
    LG --> FOOD[USDA FoodData\nnutrition API]
    LG --> CAL[Calendar tool\nmock -> Google Calendar]
    LG --> MEM[(SQLite profile store\nadherence + week plan)]
    LG --> LS[LangSmith\ntracing + monitoring]
    EV[Evals: RAGAS +\nLLM-as-judge harness] -.tests.-> API
    DEP_API[Render] -.hosts.-> API
    DEP_FE[Vercel] -.hosts.-> FE
```

### Component choices (one sentence each)

| Component | Choice | Why |
|---|---|---|
| LLM(s) | Claude Sonnet 4.5 (primary) + GPT-4o-mini (cheap judge) via **Vercel AI Gateway** | Strong tool-calling and reasoning for agent negotiation; the gateway satisfies the LLM-gateway requirement and lets me swap models with one env var. |
| Agent orchestration | **LangGraph** (supervisor pattern) | Graph-with-conditional-edges is the natural fit for a supervisor routing to specialists and looping on disagreement, and it's the framework from my cohort. |
| Tools | **Tavily** (public search), **USDA FoodData Central** (nutrition facts), **Calendar tool** (mock JSON now, Google Calendar API as stretch) | Tavily covers the "public data" requirement; USDA grounds macro math in real data; the calendar tool powers life-aware re-planning. |
| Embedding model | **OpenAI text-embedding-3-small** (direct OpenAI key, not the gateway) | Cheap, fast, strong on short semi-structured chunks like exercises and recipes. |
| Vector database | **Postgres + pgvector** (Neon in prod, local Postgres in dev) | One database for RAG chunks and LangGraph checkpoints; HNSW cosine index on `documents.embedding`. Task 6 adds BM25/full-text hybrid with RRF on top. |
| Memory | **LangGraph Postgres checkpointer** (conversation/graph state) + **SQLite** `profile.sqlite` (goals, injuries, adherence stats, week plan) | Short-term thread state in Postgres; long-term profile and workout logs in SQLite for the demo single-user setup. |
| Monitoring | **LangSmith** | One env var gives full traces of every agent hop and tool call — essential for debugging multi-agent loops. |
| Evaluation | **RAGAS** (faithfulness, context precision/recall) + custom **LLM-as-judge** rubric for coaching quality | RAGAS covers the RAG half; the judge rubric covers agent behavior (tone, safety, plan sanity). |
| User interface | **Next.js** chat + weekly-plan + upload views (`web/`) | Responsive UI on phone and laptop; typed API client to the FastAPI backend. |
| Deployment | **Split:** API on **Render** (`render.yaml`) + frontend on **Vercel** (root `web/`) | Render runs Python/uvicorn and a Sunday cron; Vercel serves the Next.js app. CORS via `FRONTEND_URL` on the API. |

### Agent workflow diagram (end to end)

```mermaid
flowchart TD
    IN[User message OR Sunday cron trigger] --> COACH[Coach agent\nsupervisor: classify intent,\nload profile memory]
    COACH -->|schedule / missed workout| SCH[Scheduler agent]
    COACH -->|food / macros| NUT[Nutrition agent]
    COACH -->|check-in / risk| ADH[Adherence agent]
    COACH -->|knowledge question| RAGQ{Personal or public?}
    RAGQ -->|personal docs| RET[Retrieve from pgvector\nuser's programs & recipes]
    RAGQ -->|public / current| TAV[Tavily web search]
    SCH --> CALT[Calendar tool:\nread conflicts, propose slots]
    NUT --> FOODT[USDA API:\nverify macros]
    NUT --> RET
    ADH --> MEMT[Memory: adherence stats,\nstreaks, drop-off signals]
    CALT --> COUNCIL{Coach reviews\nspecialist proposals}
    FOODT --> COUNCIL
    MEMT --> COUNCIL
    RET --> COUNCIL
    TAV --> COUNCIL
    COUNCIL -->|conflict: e.g. adherence\nflags overload| COACH
    COUNCIL -->|plan changed| HITL[Human approval:\none-tap accept / edit]
    COUNCIL -->|informational| OUT[Final grounded answer\nwith citations]
    HITL --> SAVE[Persist plan + state\nto memory]
    SAVE --> OUT
```

**How it works:** Every turn — whether a user message or the autonomous Sunday trigger —
enters at the Coach agent, which loads the user's profile memory and classifies intent.
Knowledge questions route through Agentic RAG: the Coach decides whether the answer lives in
the user's **own documents** (retrieve from Postgres/pgvector) or on the **public web**
(Tavily), and can use both. Action requests route to specialists: the Scheduler reads the
calendar tool and proposes a re-planned week; the Nutrition agent adjusts macros and verifies
them against the USDA API; the Adherence agent inspects streak/skip data from memory.

The Coach then reviews specialist proposals in a "council" step. This is where the agentic
behavior shows: if the Adherence agent flags drop-off risk while the Scheduler proposes a
dense week, a conditional edge loops back to the Coach, which resolves the conflict by
simplifying the plan. Any plan **change** goes through a human-in-the-loop approval
(LangGraph `interrupt`) before being persisted; informational answers return directly with
citations. All state is checkpointed so the Sunday review continues exactly where the user's
history left off.

**Requirements coverage:** LLM gateway → Vercel AI Gateway; memory → Postgres checkpointer +
SQLite profile store; runs in a browser on phone and laptop → Next.js on Vercel talking to
the public Render API URL.

---

## Task 3: Dealing with the Data

### Chunking strategy

**Markdown/structure-aware recursive splitting, ~750 tokens per chunk with 100-token
overlap** (LangChain `RecursiveCharacterTextSplitter`, with a Markdown-header splitter first
pass for structured docs, and per-recipe / per-workout-day splitting where the document
structure makes those units detectable).

Why: fitness documents are highly **unit-structured** — a training program is a list of
weeks/days, a recipe book is a list of recipes. A retrieval hit is only useful if it contains
the *whole* unit (a complete workout day with sets and reps; a full recipe with ingredients
and macros), so I split on structural boundaries first and only fall back to recursive
character splitting for prose. 750 tokens comfortably holds a full workout day or recipe;
100-token overlap protects against units that straddle boundaries.

### Data sources and external API

- **Personal data (RAG):** the user's uploaded fitness documents — their training program
  (PDF/Markdown), a personal recipe collection, and exported workout/weight logs (CSV). These
  are chunked, embedded, and stored in the Postgres `documents` table (pgvector).
- **External API #1 — Tavily (agentic search):** answers public/current questions (supplement
  safety, exercise science, "is the gym near my hotel open Sunday") that personal docs can't.
- **External API #2 — USDA FoodData Central:** authoritative macro/calorie data so the
  Nutrition agent's math is grounded rather than hallucinated.

**How they interact:** the Coach agent treats retrieval as a decision, not a default
(Agentic RAG). "What does *my* program say about deload week?" → pgvector only. "Is creatine
safe?" → Tavily only. "Plan a high-protein dinner from my recipes" → pgvector retrieves the
recipe, then USDA verifies its macros, and if the recipe collection has no match, the agent
falls back to Tavily and says so. Retrieved chunks and search results are injected into the
specialist prompts with `[doc:…]` / `[web:…]` source tags, and every grounded answer cites
its source.

---

## Task 4: End-to-End Prototype (build plan)

**Built (current stack):**

1. Core graph: Coach supervisor + all specialist agents + shared Pydantic `CouncilState` +
   **Postgres** LangGraph checkpointer (`scripts/init_db.py`).
2. Agentic RAG: `POST /api/upload` → ingestion pipeline → **pgvector** on Postgres; retrieval
   wired to the Knowledge agent; Tavily wired to the graph.
3. Scheduler + Adherence agents + council conditional edges + LangGraph `interrupt` approval
   step (`approve_node`).
4. Autonomous Sunday review: **Render cron** → `POST /internal/weekly-review` (shared secret),
   not an in-process scheduler.
5. **Next.js** chat + plan + upload UI on **Vercel**; FastAPI API on **Render** (`render.yaml`).

## Task 5: Evals (plan)

- **Test set:** ~50 examples — the 8 seed cases above expanded with synthetic variations
  generated from my own uploaded docs (so RAG questions have known gold contexts), plus
  10 adversarial cases (injury mentions, crash-diet requests → must respond safely).
- **Harness:** RAGAS (faithfulness, answer relevancy, context precision/recall) for the RAG
  path; LLM-as-judge rubric (0–5 on groundedness, plan sanity, tone, safety) for agent
  behavior; simple assertion checks for structured outputs (plan JSON validity).
- **Baseline conclusion format:** metric table before/after, per-category breakdown.

## Task 6: Improving the Prototype (plan)

- **Advanced retrieval:** add **hybrid search (dense pgvector + Postgres full-text/BM25) with
  reciprocal-rank fusion** in `app/rag/retriever.py`, because fitness queries are
  keyword-heavy ("RDL", "deload", "5x5") and exact-term sparse matching should raise context
  precision on program docs.
- **Second improvement:** upgrade the council step from single-pass to a
  critique-and-revise loop (Coach critiques specialist plan once before approval), measured
  by the LLM-judge plan-sanity score.
- Report both against the Task 5 baseline in a table.

## Task 7: Next Steps

**Keep for Demo Day:** the multi-agent council (specialist routing + risk renegotiation loop),
Agentic RAG routing between personal docs (pgvector) and Tavily, the autonomous Sunday review,
human-in-the-loop plan approval, and the eval harness with before/after numbers.

**Change/improve:** replace the mock calendar with real Google Calendar OAuth; add photo
meal logging (vision); move SQLite → Postgres for multi-user; add streaming responses in the
UI. Rationale: these raise polish and realism but none of them are needed to prove the core
agentic thesis, so they're sequenced after the evaluated core is solid.

## Final submission checklist

- [ ] Public GitHub repo (this scaffold)
- [ ] ≤10-min Loom demo (script: missed-workout re-plan → personal-doc RAG question →
      Tavily question → trigger Sunday review → show LangSmith trace → show eval table)
- [ ] This document, updated with actual eval results
- [ ] All code

# SteadyFit

An agentic AI fitness copilot for everyday people. A LangGraph **AI Coaching Team** —
Coach (supervisor) + Intake, Scheduler, Nutrition, Adherence, Knowledge — grounded in a
**curated knowledge base** (Volumes 1–7 in pgvector with **hybrid dense + FTS RRF**
retrieval), the user's own uploads, **coaching memory** (past weeks), and live web
search (Tavily). Specialists use **LLM tool calling** (`bind_tools`) for calendar,
USDA, exercise lookup, and RAG. A **context-aware scope gate** (prior-turn + pending
HITL/intake bypass) keeps chat on fitness. Conversational onboarding fills the profile
before coaching; plan changes pause for human approval.

**Multi-profile demo** (no real auth): switch personas with `X-User-Id` /
`?profile=demo-new|demo-veteran`. Profiles, plans, adherence, personal uploads, and
memories are scoped per user in Postgres.

See **deliverables.md** for the full capstone plan (Tasks 1–7).

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
  personal uploads  ──► ingest.py       ──► doc_type=personal   (user_id required; dense)
  curated KB Volumes──► ingest_kb.py    ──► doc_type=kb_*       (shared; **hybrid dense+FTS RRF**)
  weekly summaries  ──► memory_store.py ──► doc_type=memory     (user_id required; dense+recency)
App state: app_users · user_profiles · week_plans · workout_log · weight_log
Gateway: Vercel AI Gateway · Traces: LangSmith
```

```mermaid
flowchart TD
    subgraph CLIENT[Client]
        UI[Next.js on Vercel<br/>chat / plan / profile switcher]
    end

    subgraph BACKEND[Render FastAPI]
        GATE[Scope gate<br/>normalize + rate-limit]
        LG[LangGraph<br/>thread = user_id:conv]
        GW[Vercel AI Gateway<br/>Claude Sonnet / GPT-4o-mini]
        CRON[Sunday cron<br/>POST /internal/weekly-review]
    end

    subgraph AGENTS[Coaching Team]
        COACH[Coach supervisor]
        INT[Intake]
        SCH[Scheduler]
        NUT[Nutrition]
        ADH[Adherence]
        KNOW[Knowledge]
    end

    subgraph TOOLS[Agentic Tools]
        T1[Calendar mock]
        T2[USDA FoodData]
        T3[Tavily web]
        T4[exercise_lookup.json]
        T5[Hybrid retriever<br/>dense + BM25 + RRF]
    end

    subgraph STORAGE[Neon Postgres + pgvector]
        KB[doc_type kb shared Volumes]
        PERS[doc_type personal per user]
        MEM[doc_type memory weekly]
        APP[App state profiles plans logs]
    end

    subgraph OBS[Observability]
        LS[LangSmith traces]
        EV[RAGAS + LLM-judge 80 cases]
    end

    UI -->|X-User-Id| GATE
    CRON --> LG
    GATE --> LG
    LG --> GW
    LG --> COACH
    COACH --> INT
    COACH --> SCH
    COACH --> NUT
    COACH --> ADH
    COACH --> KNOW
    SCH --> T1
    SCH --> T4
    SCH --> T5
    NUT --> T2
    NUT --> T5
    ADH --> T5
    KNOW --> T3
    KNOW --> T5
    T5 --> KB
    T5 --> PERS
    T5 --> MEM
    LG --> APP
    LG --> LS
    EV -.->|tests| GATE

    style CLIENT fill:#0891b2,stroke:#164e63,color:#fff
    style BACKEND fill:#7c3aed,stroke:#4c1d95,color:#fff
    style AGENTS fill:#db2777,stroke:#831843,color:#fff
    style TOOLS fill:#16a34a,stroke:#14532d,color:#fff
    style STORAGE fill:#d97706,stroke:#78350f,color:#fff
    style OBS fill:#e11d48,stroke:#881337,color:#fff

    style UI fill:#06b6d4,stroke:#164e63,color:#fff
    style GATE fill:#8b5cf6,stroke:#4c1d95,color:#fff
    style LG fill:#8b5cf6,stroke:#4c1d95,color:#fff
    style GW fill:#8b5cf6,stroke:#4c1d95,color:#fff
    style CRON fill:#8b5cf6,stroke:#4c1d95,color:#fff
    style COACH fill:#ec4899,stroke:#831843,color:#fff
    style INT fill:#ec4899,stroke:#831843,color:#fff
    style SCH fill:#ec4899,stroke:#831843,color:#fff
    style NUT fill:#ec4899,stroke:#831843,color:#fff
    style ADH fill:#ec4899,stroke:#831843,color:#fff
    style KNOW fill:#ec4899,stroke:#831843,color:#fff
    style T1 fill:#22c55e,stroke:#14532d,color:#fff
    style T2 fill:#22c55e,stroke:#14532d,color:#fff
    style T3 fill:#22c55e,stroke:#14532d,color:#fff
    style T4 fill:#22c55e,stroke:#14532d,color:#fff
    style T5 fill:#22c55e,stroke:#14532d,color:#fff
    style KB fill:#f59e0b,stroke:#78350f,color:#fff
    style PERS fill:#f59e0b,stroke:#78350f,color:#fff
    style MEM fill:#f59e0b,stroke:#78350f,color:#fff
    style APP fill:#f59e0b,stroke:#78350f,color:#fff
    style LS fill:#f43f5e,stroke:#881337,color:#fff
    style EV fill:#f43f5e,stroke:#881337,color:#fff
```

### Turn flow (mermaid)

```mermaid
flowchart TD
    MSG[User message or Sunday cron]
    HDR[Resolve X-User-Id]
    GATE{Scope gate normalize + classify}
    REFUSE[Fixed fitness redirect]
    BOOT[Bootstrap profile + week plan]
    COACH[Coach supervisor]

    subgraph INTAKE[Onboarding]
        INT[Intake extract save ask]
        SCH1[Scheduler first WeekPlan]
    end

    subgraph SPECIALISTS[Specialists and Tools]
        SCH[Scheduler calendar exercises KB memories]
        NUT[Nutrition USDA recipes science KB]
        ADH[Adherence stats memories]
        KNOW[Knowledge personal KB web]
    end

    subgraph RETRIEVAL[Four Corpora]
        R1[Curated KB hybrid BM25 RRF]
        R2[Coaching memory recency-weighted]
        R3[Personal uploads]
        R4[Tavily web]
    end

    TEAM[Coaching team merge citations risk]
    MWRITE[memory_write weekly summary]
    HITL[Approve interrupt HITL]
    OUT[Reply citation chips quick replies]

    MSG --> HDR
    HDR --> GATE
    GATE -->|out of scope| REFUSE
    GATE -->|in scope| BOOT
    BOOT --> COACH
    COACH -->|incomplete profile| INT
    INT -->|still filling| OUT
    INT -->|confirmed| SCH1
    SCH1 --> TEAM
    COACH -->|profile change| INT
    COACH -->|schedule| SCH
    COACH -->|nutrition| NUT
    COACH -->|adherence| ADH
    COACH -->|knowledge| KNOW
    SCH --> R1
    SCH --> R2
    NUT --> R1
    NUT --> R2
    NUT --> R4
    ADH --> R2
    KNOW --> R1
    KNOW --> R3
    KNOW --> R4
    SCH --> TEAM
    NUT --> TEAM
    ADH --> TEAM
    KNOW --> TEAM
    TEAM --> MWRITE
    MWRITE -->|risk renegotiate| COACH
    MWRITE -->|plan changed| HITL
    HITL --> OUT
    MWRITE -->|informational| OUT

    style MSG fill:#4f46e5,stroke:#4338ca,color:#fff
    style OUT fill:#059669,stroke:#047857,color:#fff
    style REFUSE fill:#dc2626,stroke:#b91c1c,color:#fff
    style BOOT fill:#1e293b,stroke:#334155,color:#fff
    style COACH fill:#0f172a,stroke:#334155,color:#fff
    style TEAM fill:#b45309,stroke:#92400e,color:#fff
    style MWRITE fill:#0f172a,stroke:#334155,color:#fff
    style HITL fill:#dc2626,stroke:#b91c1c,color:#fff
    style HDR fill:#f1f5f9,stroke:#cbd5e1,color:#0f172a
    style GATE fill:#fef9c3,stroke:#ca8a04,color:#92400e
    style INT fill:#ede9fe,stroke:#c4b5fd,color:#1e1b4b
    style SCH1 fill:#ede9fe,stroke:#c4b5fd,color:#1e1b4b
    style SCH fill:#ccfbf1,stroke:#5eead4,color:#0f4c3a
    style NUT fill:#ccfbf1,stroke:#5eead4,color:#0f4c3a
    style ADH fill:#ccfbf1,stroke:#5eead4,color:#0f4c3a
    style KNOW fill:#ccfbf1,stroke:#5eead4,color:#0f4c3a
    style R1 fill:#dbeafe,stroke:#93c5fd,color:#1e3a8a
    style R2 fill:#dbeafe,stroke:#93c5fd,color:#1e3a8a
    style R3 fill:#dbeafe,stroke:#93c5fd,color:#1e3a8a
    style R4 fill:#dbeafe,stroke:#93c5fd,color:#1e3a8a
```

## Quick start

### Backend (API)

```bash
uv sync
cp .env.example .env        # fill in API keys and DATABASE_URL
uv run python scripts/init_db.py
uv run python scripts/migrate_documents_kb.py   # KB metadata columns (idempotent)
uv run python scripts/migrate_documents_memory.py  # multi-user memory upsert index
uv run python scripts/migrate_add_fts.py        # content_tsv + GIN for hybrid retrieval
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
# Or rely on seed_memory --profile veteran, which ingests data/eval_uploads/*
curl -H "X-User-Id: demo-veteran" -F "file=@data/eval_uploads/my_program.md" http://localhost:8000/api/upload
```

Tests and evals:
```bash
uv run pytest tests/
uv run python evals/run_evals.py --label hybrid_retrieval   # 80 cases → summary_hybrid_retrieval.*
uv run python evals/compare.py --a baseline_fixed --b hybrid_retrieval
# Categories (13): schedule, nutrition, adherence, knowledge, safety, autonomous,
#   adversarial, onboarding, kb_retrieval, rag_personal, rag_web, memory, gate_context
# RAGAS (faithfulness, answer_relevancy, context_precision/recall, answer_correctness)
# on rag_* / kb_retrieval / memory. Local harness forces LangSmith tracing off.
# Artifacts: evals/summary_baseline_fixed.md, summary_hybrid_retrieval.md,
#   comparison_baseline_fixed_vs_hybrid_retrieval.md
```

**LangSmith (optional):**
```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=steadyfit-dev
# Full experiment: uv run python evals/run_evals.py --experiment
# Chat/API tracing: see TRACING.md
```

## Deploy

**API (Render):** `render.yaml` — web service + Sunday cron. Set secrets from `.env.example`.

**Frontend (Vercel):** Root Directory = `web`, set
`NEXT_PUBLIC_API_URL=https://<your-render-api>.onrender.com`.

CORS: `FRONTEND_URL` on Render to your Vercel origin.

## Repo map

```
app/
  main.py / chat_pipeline.py / security.py   # scope gate, chat/approve/profiles APIs
  graph/          coach, intake, specialists, coaching_team, memory_write, approve, tool_agent
  rag/            ingest.py · ingest_kb.py · memory_store.py · retriever.py (dense + hybrid RRF)
  tools/          calendar, food_api, tavily, exercise_lookup, agent_tools (@tool)
  memory/         Postgres profiles + adherence + weekly_summary + user_context
web/              Next.js — chat (chips + citations), plan, update/upload, profile switcher
data/knowledge_base/   Volume1–7 markdown + exercise_library.json
evals/            golden_dataset.jsonl (80) + harness + compare.py + labeled results
data/eval_uploads/ personal fixtures for rag_personal (seeded onto demo-veteran)
scripts/          init_db, migrate_documents_*, migrate_add_fts, seed_memory, backfill_memories
tests/            routing, HITL, gate_context, hybrid RRF, KB, memory isolation, security
deliverables.md   Capstone Tasks 1–7 (incl. hybrid before/after)
TRACING.md        LangSmith setup
```

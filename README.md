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

See **PLAN.md** for the full capstone plan (Tasks 1–7).

## Architecture

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#0f172a",
    "primaryTextColor": "#ffffff",
    "primaryBorderColor": "#1e293b",
    "lineColor": "#64748b",
    "background": "#f8fafc",
    "fontFamily": "system-ui, sans-serif",
    "edgeLabelBackground": "#f1f5f9",
    "clusterBkg": "#f1f5f9",
    "clusterBorder": "#cbd5e1"
  }
}}%%
flowchart LR
    subgraph CLIENT["🖥️  Client"]
        UI["📱 Next.js · Vercel\nchat · plan · profile switcher\n?profile= · X-User-Id"]
    end

    subgraph BACKEND["⚙️  Render · FastAPI"]
        GATE["🛡️ Scope gate\nnormalize · rate-limit"]
        LG["🧠 LangGraph\nthread = user_id:conv\nPostgres checkpointer"]
        GW["☁️ Vercel AI Gateway\nClaude Sonnet · GPT-4o-mini"]
        CRON["⏰ Sunday cron\nPOST /internal/weekly-review"]
    end

    subgraph AGENTS["🤝  Coaching Team"]
        COACH["🎯 Coach\nsupervisor"]
        INT["📝 Intake"]
        SCH["📆 Scheduler"]
        NUT["🥗 Nutrition"]
        ADH["💪 Adherence"]
        KNOW["📚 Knowledge"]
    end

    subgraph TOOLS["🔧  Agentic Tools"]
        direction TB
        T1["📅 Calendar mock"]
        T2["🥗 USDA FoodData"]
        T3["🌐 Tavily web"]
        T4["📦 exercise_lookup.json"]
        T5["🔍 Hybrid retriever\ndense + BM25 + RRF"]
    end

    subgraph STORAGE["🗄️  Neon Postgres + pgvector"]
        direction TB
        KB["📖 doc_type=kb_*\nVolumes 1–7 · shared"]
        PERS["📄 doc_type=personal\nper user_id"]
        MEM["🧠 doc_type=memory\nweekly summaries · per user_id"]
        APP["💿 App state\nprofiles · plans · logs"]
    end

    subgraph OBS["📊  Observability"]
        LS["🔭 LangSmith\ntraces · tool calls"]
        EV["🧪 RAGAS + LLM-judge\n80 cases"]
    end

    UI -->|"X-User-Id"| GATE
    CRON --> LG
    GATE --> LG --> GW
    LG --> COACH
    COACH --> INT & SCH & NUT & ADH & KNOW
    SCH & NUT & ADH & KNOW --> T1 & T2 & T3 & T4 & T5
    T5 --> KB & PERS & MEM
    LG --> APP & LS
    EV -.->|"tests"| GATE

    style CLIENT fill:#f0f9ff,stroke:#bae6fd,color:#0f172a
    style BACKEND fill:#1e293b,stroke:#334155,color:#fff
    style AGENTS fill:#4f46e5,stroke:#4338ca,color:#fff
    style TOOLS fill:#0f766e,stroke:#0d9488,color:#fff
    style STORAGE fill:#7c3aed,stroke:#6d28d9,color:#fff
    style OBS fill:#b45309,stroke:#92400e,color:#fff
    style UI fill:#dbeafe,color:#1e3a8a,stroke:#93c5fd
    style GATE fill:#e2e8f0,color:#0f172a,stroke:#94a3b8
    style LG fill:#ede9fe,color:#1e1b4b,stroke:#c4b5fd
    style GW fill:#ede9fe,color:#1e1b4b,stroke:#c4b5fd
    style CRON fill:#e2e8f0,color:#0f172a,stroke:#94a3b8
    style COACH fill:#c7d2fe,color:#1e1b4b,stroke:#818cf8
    style INT fill:#c7d2fe,color:#1e1b4b,stroke:#818cf8
    style SCH fill:#c7d2fe,color:#1e1b4b,stroke:#818cf8
    style NUT fill:#c7d2fe,color:#1e1b4b,stroke:#818cf8
    style ADH fill:#c7d2fe,color:#1e1b4b,stroke:#818cf8
    style KNOW fill:#c7d2fe,color:#1e1b4b,stroke:#818cf8
    style T1 fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style T2 fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style T3 fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style T4 fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style T5 fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style KB fill:#ede9fe,color:#1e1b4b,stroke:#c4b5fd
    style PERS fill:#ede9fe,color:#1e1b4b,stroke:#c4b5fd
    style MEM fill:#ede9fe,color:#1e1b4b,stroke:#c4b5fd
    style APP fill:#ede9fe,color:#1e1b4b,stroke:#c4b5fd
    style LS fill:#fef3c7,color:#78350f,stroke:#fcd34d
    style EV fill:#fef3c7,color:#78350f,stroke:#fcd34d
```

### Turn flow (mermaid)

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "primaryColor": "#1e293b",
    "primaryTextColor": "#ffffff",
    "lineColor": "#94a3b8",
    "background": "#f8fafc",
    "fontFamily": "system-ui, sans-serif",
    "edgeLabelBackground": "#f1f5f9"
  }
}}%%
flowchart TD
    MSG(["💬 User message\nOR Sunday cron"])
    HDR["👤 Resolve X-User-Id"]
    GATE{"🛡️ Scope gate\nnormalize + classify"}
    REFUSE(["🚫 Fixed fitness\nredirect"])
    BOOT["⚙️ Bootstrap\nprofile + week plan"]
    COACH["🎯 Coach\nsupervisor"]

    subgraph INTAKE["📝  Onboarding"]
        INT["Intake node\nextract → save → ask one question"]
        SCH1["Scheduler\nfirst WeekPlan"]
    end

    subgraph SPECIALISTS["🤝  Specialists + Tools"]
        SCH["📆 Scheduler\ncalendar · exercises · KB · memories"]
        NUT["🥗 Nutrition\nUSDA · recipes · science KB"]
        ADH["💪 Adherence\nstats · memories"]
        KNOW["📚 Knowledge\npersonal · KB · web"]
    end

    subgraph RETRIEVAL["🔍  Four Corpora"]
        R1["📖 Curated KB\nhybrid BM25 + RRF"]
        R2["🧠 Coaching memory\nrecency-weighted"]
        R3["📄 Personal uploads"]
        R4["🌐 Tavily web"]
    end

    TEAM["⚖️ Coaching team merge\ncitations · risk check"]
    MWRITE["💾 memory_write\nweekly summary upsert"]
    HITL(["✋ Approve interrupt\nhuman-in-the-loop"])
    OUT(["✅ Reply\ncitation chips · quick replies"])

    MSG --> HDR --> GATE
    GATE -->|"out of scope"| REFUSE
    GATE -->|"in scope"| BOOT --> COACH
    COACH -->|"incomplete profile"| INT
    INT -->|"still filling"| OUT
    INT -->|"confirmed"| SCH1 --> TEAM
    COACH -->|"profile change"| INT
    COACH -->|"schedule"| SCH
    COACH -->|"nutrition"| NUT
    COACH -->|"adherence"| ADH
    COACH -->|"knowledge"| KNOW
    SCH & NUT --> R1 & R2
    ADH --> R2
    KNOW --> R1 & R3 & R4
    NUT --> R4
    SCH & NUT & ADH & KNOW --> TEAM
    TEAM --> MWRITE
    MWRITE -->|"risk renegotiate"| COACH
    MWRITE -->|"plan changed"| HITL --> OUT
    MWRITE -->|"informational"| OUT

    style MSG fill:#4f46e5,color:#fff,stroke:#4338ca
    style OUT fill:#059669,color:#fff,stroke:#047857
    style REFUSE fill:#dc2626,color:#fff,stroke:#b91c1c
    style BOOT fill:#1e293b,color:#fff,stroke:#334155
    style COACH fill:#0f172a,color:#fff,stroke:#334155
    style TEAM fill:#b45309,color:#fff,stroke:#92400e
    style MWRITE fill:#0f172a,color:#fff,stroke:#334155
    style HITL fill:#dc2626,color:#fff,stroke:#b91c1c
    style HDR fill:#f1f5f9,color:#0f172a,stroke:#cbd5e1
    style GATE fill:#fef9c3,color:#92400e,stroke:#ca8a04
    style INTAKE fill:#7c3aed,stroke:#6d28d9,color:#fff
    style INT fill:#ede9fe,color:#1e1b4b,stroke:#c4b5fd
    style SCH1 fill:#ede9fe,color:#1e1b4b,stroke:#c4b5fd
    style SPECIALISTS fill:#0f766e,stroke:#0d9488,color:#fff
    style SCH fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style NUT fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style ADH fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style KNOW fill:#ccfbf1,color:#0f4c3a,stroke:#5eead4
    style RETRIEVAL fill:#1e3a5f,stroke:#1e40af,color:#fff
    style R1 fill:#dbeafe,color:#1e3a8a,stroke:#93c5fd
    style R2 fill:#dbeafe,color:#1e3a8a,stroke:#93c5fd
    style R3 fill:#dbeafe,color:#1e3a8a,stroke:#93c5fd
    style R4 fill:#dbeafe,color:#1e3a8a,stroke:#93c5fd
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
PLAN.md           Capstone Tasks 1–7 (incl. hybrid before/after)
TRACING.md        LangSmith setup
```

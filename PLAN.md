# SteadyFit — Capstone Plan & Architecture

An agentic AI fitness copilot for everyday people, built as a multi-agent LangGraph system
with Agentic RAG over a **curated SteadyFit knowledge base** plus the user's own uploads,
**coaching memory** from past weeks, **LLM tool calling**, conversational onboarding,
**multi-profile** demo tenants (no real auth), and human-in-the-loop plan approval.

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
| 1 | "I missed Monday's leg day and I'm traveling Wed–Fri with only a hotel gym." | Redistributed week; hotel-friendly **kb_id** substitutions via exercise lookup; no guilt language. |
| 2 | "I had biryani and a mango lassi at a work lunch." | Reasonable calorie/macro estimate; remaining-day guidance; no shaming. |
| 3 | "How do I do a proper push-up?" | Grounded in **KB** `Chest.md` with `[KB: …]` citation. |
| 4 | "Is creatine safe to take daily?" | Web and/or KB science; safe framing. |
| 5 | Sunday review trigger (no user input) | Autonomous weekly summary + next-week proposal + approval request. |
| 6 | User has skipped 3 sessions in 10 days | Adherence flags RISK; plan **simplified**. |
| 7 | "How much protein to build muscle?" | NutritionScience KB (~1.6–2.2 g/kg) + citation. |
| 8 | New user with empty profile | Conversational **intake** (goal → sessions → modes → food → optional age/sex/constraints). |
| 9 | Returning traveler ("hotel gym again") | Cites past travel **Memory** week; proposes short hotel sessions that worked before. |

---

## Task 2: Propose a Solution

### Solution (one sentence)

SteadyFit is a proactive multi-agent fitness copilot — LangGraph Coach + specialists with
**agentic tool calling**, a curated metadata-rich **knowledge base**, personal-doc RAG,
**coaching memory**, live web search, multi-profile Postgres state, profile intake, and
HITL plan approval — that re-plans training and nutrition around real life.

### Infrastructure diagram

```mermaid
flowchart TD
    U[Browser UI\nchat · plan · update\nprofile switcher] --> FE[Next.js\nVercel]
    FE -->|X-User-Id\n?profile=| API[FastAPI\nRender]
    CRON[Sunday cron] --> API
    API --> GATE[Scope gate + normalize]
    GATE --> LG[LangGraph\nCoachingTeamState\nthread = user_id:conv]
    LG --> GW[Vercel AI Gateway]
    LG --> TOOLS[bind_tools loop]
    TOOLS --> CAL[Calendar mock]
    TOOLS --> FOOD[USDA FoodData]
    TOOLS --> TAV[Tavily]
    TOOLS --> XL[exercise_lookup JSON]
    TOOLS --> RET[Retriever\nfilter-then-rank]
    RET --> PG[(Postgres + pgvector\ndocuments + checkpointer)]
    KB[ingest_kb\nVolumes 1–7] --> PG
    UP[Personal uploads] --> ING[ingest.py] --> PG
    LG --> MEMW[memory_write] --> PG
    LG --> APP[(Postgres app state\nusers · profiles · plans · logs)]
    LG --> LS[LangSmith]
    EV[Evals harness] -.tests.-> API
```

### Component choices (one sentence each)

| Component | Choice | Why |
|---|---|---|
| LLM(s) | Claude Sonnet 4.5 (primary) + GPT-4o-mini (judge / intake extract) via **Vercel AI Gateway** | Tool-calling + cheap structured classification; swap models with env vars. |
| Agent orchestration | **LangGraph** supervisor + specialists + coaching_team + memory_write | Completeness gate → intake; risk renegotiation; HITL `interrupt`; weekly memory upsert. |
| Tools | **Tavily**, **USDA**, **calendar mock**, **exercise_lookup**, **retrieve_*** | Selection via deterministic filters; explanation via semantic KB/personal/web/memory. |
| Embedding | **text-embedding-3-small** | Short exercise/guide/memory chunks. |
| Vector DB | **Postgres + pgvector** with KB metadata + `user_id` on personal/memory rows | Shared KB (`user_id` NULL) stays isolated from tenant data. |
| App memory | Postgres **`app_users` / profiles / week_plans / workout_log / weight_log`** | Multi-profile demo via `X-User-Id`; no SQLite. |
| Coaching memory | `documents` `doc_type=memory` + recency-weighted retrieve | Scheduler/Adherence recall past travel / overload weeks with `[Memory: …]` citations. |
| Monitoring | **LangSmith** | Traces of tool_calls and agent hops; optional `--experiment` runs. |
| Evaluation | RAGAS + LLM-as-judge; **74** cases incl. adversarial / onboarding / **kb_retrieval** / **rag_personal** / **memory** | Onboarding → `demo-new`; all others → `demo-veteran` (+ seeded personal uploads). |
| UI | **Next.js** — chat chips, citation pills, plan approve, **profile dropdown** | Shareable `?profile=` links; header sends `X-User-Id` on every call. |
| Deploy | Render API + Vercel `web/` | Cron weekly review loops **all** profiles. |

### Agent workflow diagram (end to end)

```mermaid
flowchart TD
    IN[User message OR Sunday cron] --> UID[Resolve user_id]
    UID --> SG{Scope gate}
    SG -->|OOS| REJ[Fitness-only refusal]
    SG -->|OK| COACH[Coach\nload profile]
    COACH -->|incomplete profile| INT[Intake node\nextract → persist → one question]
    INT -->|still filling| END1[END + quick_replies]
    INT -->|confirmed| FIRST[first_plan → Scheduler]
    COACH -->|profile update| INT
    COACH -->|schedule| SCH[Scheduler]
    COACH -->|nutrition| NUT[Nutrition]
    COACH -->|adherence| ADH[Adherence]
    COACH -->|knowledge| KNOW[Knowledge]
    SCH --> TL1[Tools: calendar · exercises · KB · memories]
    NUT --> TL2[Tools: USDA · recipes · nutrition science KB]
    ADH --> TL3[Tools: adherence_stats · memories]
    KNOW --> TL4[Tools: personal · KB · web]
    FIRST --> TL1
    TL1 --> TEAM[Coaching team merge\n+ citations]
    TL2 --> TEAM
    TL3 --> TEAM
    TL4 --> TEAM
    TEAM --> MWRITE[memory_write\nweekly-review upsert]
    MWRITE -->|risk + dense plan| COACH
    MWRITE -->|plan_changed| HITL[approve interrupt]
    MWRITE -->|informational| OUT[Reply + citation chips]
    HITL --> SAVE[Persist week plan]
    SAVE --> OUT
```

**How it works:** Each request carries **`X-User-Id`**. Threads are namespaced
`{user_id}:{conversation_id}` so checkpointer state never crosses personas. Chat enters a
**scope gate** (with fitness-hint fast path during intake). The Coach loads that user's
Postgres profile; if onboarding is incomplete it routes to **intake**. After confirmation,
**first_plan** runs the Scheduler with KB templates + exercise IDs. Otherwise specialists
call tools via `bind_tools`. Knowledge is three-way: personal uploads \| curated KB \|
Tavily. Scheduler and Adherence also retrieve **user-scoped coaching memories**. The
coaching team merges proposals and preserves `[KB: …]` / `[Memory: …]` / `[doc:…]` /
`[web:…]` citations. On weekly-review turns, **memory_write** upserts a structured weekly
summary into pgvector. Plan changes hit HITL approve.

**Demo personas:** `demo-new` (empty onboarding) and `demo-veteran` (~12 weeks of logs +
travel/overload memories). Frontend profile switcher uses `?profile=` (not localStorage for
the active identity).

---

## Task 3: Dealing with the Data

### Chunking strategy

**Three paths:**

1. **Personal uploads** (`app/rag/ingest.py`): markdown-header then recursive split (~750 tokens /
   3000 chars, overlap) — good for free-form programs/recipes. Always stored with `user_id`.
2. **Curated KB** (`app/rag/ingest_kb.py`): split on `##` (one exercise/section = one chunk);
   if a section exceeds ~1200 tokens, split on `###`. Parse YAML metadata into columns
   (`kb_id`, muscles, equipment, modality, difficulty, contraindications). **Shared** —
   `user_id` is NULL; never deleted on profile reset.
3. **Coaching memory** (`app/rag/memory_store.py`): one embedded summary per
   `(user_id, week_start)` with context tags; retrieve with cosine × **recency weight**.

### Data sources

| Source | Store | Role |
|---|---|---|
| Volumes 1–7 (`data/knowledge_base/`) | pgvector `doc_type=kb_*`, `user_id` NULL | Shared technique, guides, templates, science |
| `exercise_library.json` | In-process index | Structured `find_exercises` / `get_substitutions` |
| User uploads | pgvector `doc_type=personal`, `user_id` set | Private programs/recipes |
| Weekly summaries | pgvector `doc_type=memory`, `user_id` set | Travel / overload precedents for re-planning |
| Tavily | Live | Current / public facts |
| USDA | Live | Macro grounding |
| Postgres app tables | `app_users`, `user_profiles`, `week_plans`, `workout_log`, `weight_log` | Onboarding slots, plans, adherence |

**Rule of thumb:** structured lookup for **selection**; semantic RAG for **explanation**;
memory for **“what worked for this person before.”**

---

## Task 4: End-to-End Prototype (built)

1. Graph: Coach → Intake \| Scheduler \| Nutrition \| Adherence \| Knowledge → Coaching team →
   **memory_write** → Approve \| END; Postgres checkpointer pool.
2. Agentic tools on specialists (`app/graph/tool_agent.py` + `app/tools/agent_tools.py`).
3. Curated KB ingest + metadata-filtered retrieve; personal path kept separate.
4. Conversational onboarding + `seed_memory.py --profile fresh|veteran`; UI chips + citations.
5. Scope gate + rate limit + `<untrusted>` wrappers.
6. Sunday cron weekly review **for every profile**; Next.js on Vercel + API on Render.
7. **Multi-profile:** `X-User-Id`, thread namespacing, profile switcher, isolation tests.
8. **Coaching memory:** weekly summarizer + recency-weighted retrieve + memory evals.
9. **Personal eval fixtures:** `data/eval_uploads/` ingested for `demo-veteran` (rag_personal).

---

## Task 5: Evals

- Golden set: **74 cases** across schedule / nutrition / knowledge / safety / adversarial /
  autonomous / onboarding / **kb_retrieval** / **rag_personal** / **rag_web** / **memory**.
- Harness: LLM-as-judge (groundedness, plan sanity, tone, safety) + RAGAS for
  `rag_*` / `kb_retrieval` when context is present.
- Profile mapping: onboarding → `demo-new`; all other categories → `demo-veteran`
  (veteran seed includes `data/eval_uploads/` for personal RAG).
- Run: `uv run python evals/run_evals.py` → `evals/summary.md`.
- Optional LangSmith: `uv run python evals/run_evals.py --experiment`.

### Latest full-suite averages (50 cases, pre–memory-id expansion)

| Metric | Avg (0–5) |
|---|---|
| groundedness | 4.50 |
| plan_sanity | 4.56 |
| tone | 4.74 |
| safety | 4.74 |

Category highlights: **kb_retrieval** 5.0 groundedness; **schedule** / **safety** / **knowledge** strong;
**adversarial** and some **nutrition** / **rag_personal** cases pull averages down.
Memory cases **51–53** scored well in a targeted re-run (judge ~4.7–5.0) after coaching memory shipped.

**Golden set (current):** **74** cases — `kb_retrieval` (29) + `rag_personal` (14) emphasize curated KB vs
user-upload RAG. Personal fixtures live in `data/eval_uploads/` and are ingested for
`demo-veteran` by `scripts/seed_memory.py --profile veteran`. Re-run the full suite before
publishing a new LangSmith baseline.

---

## Task 6: Improving the Prototype

**Shipped:**

| Improvement | Status |
|---|---|
| Metadata-filtered dense retrieval (doc_type / modality) | Done |
| Structured exercise index + substitutions tools | Done |
| KB section-aware ingest + citations in UI | Done |
| Agentic `bind_tools` loops | Done |
| Multi-profile Postgres + `X-User-Id` demo tenants | Done |
| Coaching memory (`doc_type=memory`) + recency weighting | Done |
| Hybrid BM25 + RRF | Still optional stretch |
| Council critique-and-revise loop | Stretch — coaching_team is still single-pass merge |

Report before/after on `kb_retrieval` + schedule + memory cases after a full eval run.

---

## Task 7: Next Steps

**Keep for Demo Day:** switch `demo-new` → intake → first plan approve; switch
`demo-veteran` → hotel re-plan with **Memory** citation; KB technique question with chips;
LangSmith tool_call traces; eval table.

**Change/improve later:** real auth (Clerk/Auth0) instead of header switcher; Google Calendar
OAuth; vision meal logging; streaming UI; BM25 hybrid; council critique pass.

---

## Final submission checklist

- [ ] Public GitHub repo
- [ ] ≤10-min Loom (intake on demo-new → hotel/memory on demo-veteran → KB cite →
      Tavily/creatine → Sunday review → LangSmith → eval table)
- [x] This document updated with **actual eval numbers** (50-case suite + targeted memory run)
- [x] Architecture docs (README + PLAN) aligned with current code
- [x] Code (graph, KB, tools, onboarding, multi-profile memory, UI)

# SteadyFit — Improvements Log

Chronological log of product and eval upgrades after the Task 5 baseline
(`baseline_fixed`, 80 cases) and Task 6 hybrid retrieval (`hybrid_retrieval`).
Artifacts live under `evals/summary_*.md` / `evals/results_*.json`.

**Live:** [App](https://steady-fit.vercel.app) · [API](https://steadyfit-api.onrender.com/health)

**Golden set (current):** **115** cases in `evals/golden_dataset.jsonl`
(22 categories). Latest near-full suite: `try_profile_ux_full` (**96** cases,
0 critical must-pass failures).

---

## Task 5 → Task 6 (retrieval + gate)

| Change | Evidence |
|---|---|
| Hybrid dense + BM25 + RRF for curated KB | `kb_retrieval` context_precision 0.107 → 0.161 (+50%); `summary_hybrid_retrieval.md`, `comparison_baseline_fixed_vs_hybrid_retrieval.md` |
| Context-aware scope gate (prior turn + pending HITL/intake bypass) | `gate_context` false positives 4 → 0; adversarial safety 3.12 → 5.0 after golden fixes |

---

## Post–Task 6 product upgrades (shipped)

### 1. Council critique-and-revise (pre-merge)

Specialist plan drafts pass a Coach critique node (max 1 revise cycle) before the
coaching-team merge. Hard failures (knee contraindications, veg/non-veg preference
mismatches, sessions mismatch) trigger a revise; soft nitpicks stay clean.

| Suite | N | Result |
|---|---|---|
| `council_critique` | 4 | Judge all 5.0; must-pass structural checks for revise / clean / skip / cap |
| `council_critique_full` | 92 | groundedness 4.68 · plan_sanity 4.82 · tone 4.90 · safety 4.91 |
| `critique_interrupt_fix` | 92 | **0** critical must-pass failures; safety 4.96 |

Artifacts: `evals/summary_council_critique.md`, `summary_council_critique_full.md`,
`summary_critique_interrupt_fix.md`.

### 2. Vision / photo meal logging

Chat photo → vision food ID → USDA macros → `food_log` (no image retained).
Critique skipped on meal-log-only turns. Non-food and adversarial-in-image notes
are handled safely.

| Suite | N | Result |
|---|---|---|
| `photo_meal` | 5 | Judge all 5.0; **0** critical failures (clear meal, ambiguous portion, non-food, injection-in-notes, critique-skip) |

Artifacts: `evals/summary_photo_meal.md`.

### 3. Try-it-yourself ephemeral profiles

`POST /api/profiles/try` creates a guest `try-*` profile (48h TTL, rate-limited).
UI “Try it yourself” path — no demo persona required. Daily cleanup cron in
`render.yaml`.

| Suite | N | Result |
|---|---|---|
| `try_profile_ux` / `try_profile_ux_full` | 96 (full) | **0** critical must-pass; groundedness 4.87 · plan_sanity 4.89 · tone 4.91 · safety 4.96 |

Artifacts: `evals/summary_try_profile_ux_full.md`.

### 4. Topic / safety interrupts + first-message scope

Pregnancy / pain / allergy mid-offer interrupt routing; first-message scope
hardening so cold-start fitness asks are not false-refused.

| Suite | N | Result |
|---|---|---|
| `topic_interrupt_fix` | 88 | 0 critical must-pass |
| `first_message_fix` | (category) | CRITICAL cold-start cases in golden set |
| `scope_gate_hardening` | labeled suite | Gate false-positive regression coverage |

### 5. Weight / diet metrics gate + Phase 1 diet plan

Hard-stop before first WeekPlan: **weight → target weight → height → activity**
(one question per turn). Code-computed Mifflin–St Jeor macros (`app/graph/tdee.py`);
KB Indian meal week (`diet_plan_days`); approval card + Plan page **planned vs
logged** meals. Preference-safe rebuild in critique for vegetarian/vegan.

| Suite | N | Result |
|---|---|---|
| `weight_gate` | 5 | Structural hard-stop + multi-turn chain |
| `diet_plan` | 4 | **0** critical; approval includes diet + TDEE macros; veg-safe |
| `intake_chips` | 4 | Bare chip `"4"` → sessions (not age) |

Artifacts: `evals/summary_diet_plan.md`, `summary_weight_gate_*.md`,
`summary_intake_chips_bare_numeral.md`.

### 6. Approval-card framing + daily food totals

First-plan vs tweak headlines on HITL card; `GET /api/food_log/today` SUM totals
for Nutrition “remaining today” and Plan page logged section.

---

## Eval inventory (how to read the numbers)

| Label / artifact | Cases | Notes |
|---|---|---|
| `baseline_fixed` | 80 | Task 5 baseline (pre-hybrid) |
| `hybrid_retrieval` | 80 | Task 6 hybrid RRF |
| `try_profile_ux_full` | **96** | Latest near-full suite (0 critical) |
| `critique_interrupt_fix` | 92 | Post critique + interrupt fixes |
| `golden_dataset.jsonl` (HEAD) | **115** | Current committed case count |

Run subsets:
```bash
uv run python evals/run_evals.py --label try_profile_ux_full
uv run python evals/run_evals.py --category diet_plan --label diet_plan
uv run python evals/run_evals.py --category photo_meal --label photo_meal
uv run python evals/run_evals.py --category council_critique --label council_critique
```

---

## Still future (not claimed as shipped)

- Real auth (Clerk/Auth0) instead of `X-User-Id` / try-profile switcher
- Google Calendar OAuth (mock calendar remains)
- Streaming UI tokens
- Meal swap / diet adherence tracking (explicitly out of Phase 1 diet scope)
- Faithfulness prompt hardening for hybrid-retrieval specificity gap

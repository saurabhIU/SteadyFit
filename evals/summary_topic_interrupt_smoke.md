# Eval summary (`topic_interrupt_smoke`)

Total cases: 4

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 3.75 |
| plan_sanity | 5.0 |
| tone | 5.0 |
| safety | 5.0 |

## CRITICAL must-pass failures

None.

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | — |
| answer_relevancy | — |
| context_precision | — |
| context_recall | — |
| answer_correctness | — |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|

## Judge scores by category

- **gate_context** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **topic_interrupt** (3): groundedness=3.33, plan_sanity=5.0, tone=5.0, safety=5.0

# Eval summary (`topic_interrupt_fix`)

Total cases: 88

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.72 |
| plan_sanity | 4.84 |
| tone | 4.9 |
| safety | 4.98 |

## CRITICAL must-pass failures

None.

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.5092 |
| answer_relevancy | 0.6129 |
| context_precision | 0.4062 |
| context_recall | 0.25 |
| answer_correctness | 0.3024 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 30 | 0.4464 | 0.6878 | 0.1429 | 0.1071 | 0.2307 |
| memory | 3 | 0.4627 | 0.3655 | 0.6667 | 0.6667 | 0.1588 |
| rag_personal | 14 | 0.6369 | 0.5151 | 0.9286 | 0.5 | 0.5251 |
| rag_web | 3 | 0.5464 | 0.6171 | 0.1667 | 0.0 | 0.0761 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 7 | rag_personal | 1 | 0.642857 | 0.872365 | 1.0 | 0.5 | 0.53046 |  |
| 8 | rag_personal | 1 | 1.0 | 0.0 | 1.0 | 0.5 | 0.749893 |  |
| 9 | rag_personal | 1 | 0.769231 | 0.825537 | 1.0 | 0.0 | 0.64653 |  |
| 10 | rag_web | 2 | 0.777778 | 0.965867 | 0.5 | 0.0 | 0.054628 |  |
| 11 | rag_web | 2 | 0.4 | 0.0 | 0.0 | 0.0 | 0.093098 |  |
| 12 | rag_web | 3 | 0.461538 | 0.885312 | 0.0 | 0.0 | 0.080654 |  |
| 15 | kb_retrieval | 2 | 0.733333 | 0.694055 | 0.0 | 0.0 | 0.794598 |  |
| 27 | kb_retrieval | 3 | 0.333333 | 1.0 | 0.0 | 0.0 | 0.04823 |  |
| 33 | kb_retrieval | 2 | 0.833333 | 0.883318 | 0.0 | 0.0 | 0.131259 |  |
| 34 | kb_retrieval | 3 | 0.592593 | 0.846404 | 1.0 | 0.5 | 0.220273 |  |
| 35 | kb_retrieval | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.172711 |  |
| 36 | kb_retrieval | 4 | 0.1875 | 0.895507 | 0.0 | 0.0 | 0.049651 |  |
| 37 | kb_retrieval | 4 | 0.785714 | 0.759144 | 1.0 | 0.5 | 0.131418 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 2 | 0.842105 | 0.856913 | 0.5 | 0.0 | 0.140072 |  |
| 40 | kb_retrieval | 2 | 0.818182 | 0.928323 | 0.0 | 0.0 | 0.143515 |  |
| 41 | kb_retrieval | 4 | 0.038462 | 0.564383 | 0.0 | 0.0 | 0.103109 |  |
| 42 | kb_retrieval | 4 | 0.3125 | 0.0 | 0.5 | 1.0 | 0.16084 |  |
| 43 | kb_retrieval | 2 | 0.944444 | 0.880671 | 0.0 | 0.0 | 0.112133 |  |
| 44 | kb_retrieval | 1 | 0.0 | 0.794356 | 0.0 | 0.0 | 0.11387 |  |
| 45 | kb_retrieval | 2 | 0.925926 | 0.891929 | 0.5 | 0.0 | 0.137329 |  |
| 46 | kb_retrieval | 2 | 0.894737 | 0.776768 | 0.0 | 0.0 | 0.815286 |  |
| 47 | kb_retrieval | 3 | 0.076923 | 0.711312 | 0.0 | 0.0 | 0.115357 |  |
| 48 | kb_retrieval | 4 | 0.142857 | 0.362788 | 0.0 | 0.0 | 0.166128 |  |
| 49 | kb_retrieval | 2 | 0.888889 | 0.895057 | 0.0 | 0.0 | 0.12035 |  |
| 50 | kb_retrieval | 2 | 0.0 | 0.707206 | 0.0 | 0.0 | 0.134391 |  |
| 51 | memory | 3 | 0.588235 | 0.58511 | 1.0 | 1.0 | 0.284553 |  |
| 52 | memory | 3 | 0.8 | 0.0 | 1.0 | 1.0 | 0.11944 |  |
| 53 | memory | 1 | 0.0 | 0.511524 | 0.0 | 0.0 | 0.072446 |  |
| 54 | rag_personal | 1 | 0.875 | 0.598519 | 1.0 | 0.5 | 0.835415 |  |
| 55 | rag_personal | 1 | 0.888889 | 0.804164 | 1.0 | 0.5 | 0.45599 |  |
| 56 | rag_personal | 4 | 0.125 | 0.0 | 1.0 | 0.5 | 0.284148 |  |
| 57 | rag_personal | 1 | 0.764706 | 0.0 | 1.0 | 0.5 | 0.594038 |  |
| 58 | rag_personal | 1 | 0.454545 | 0.599132 | 1.0 | 0.5 | 0.395749 |  |
| 59 | rag_personal | 1 | 0.666667 | 0.0 | 1.0 | 0.5 | 0.488215 |  |
| 60 | rag_personal | 4 | 0.0625 | 0.0 | 1.0 | 0.5 | 0.206105 |  |
| 61 | rag_personal | 1 | 0.666667 | 0.808298 | 1.0 | 0.5 | 0.838504 |  |
| 62 | rag_personal | 1 | 1.0 | 0.96735 | 0.0 | 1.0 | 0.317379 |  |
| 63 | kb_retrieval | 2 | 0.529412 | 0.781288 | 0.0 | 0.5 | 0.300453 |  |
| 64 | kb_retrieval | 2 | 0.708333 | 0.0 | 0.0 | 0.0 | 0.238514 |  |
| 65 | kb_retrieval | 3 | 0.32 | 0.779349 | 0.0 | 0.0 | 0.542725 |  |
| 66 | kb_retrieval | 2 | 0.789474 | 0.847752 | 0.5 | 0.5 | 0.223958 |  |
| 67 | kb_retrieval | 1 | 0.0 | 0.878721 | 0.0 | 0.0 | 0.128452 |  |
| 68 | kb_retrieval | 2 | 0.8 | 0.911808 | 0.0 | 0.0 | 0.786121 |  |
| 69 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 70 | kb_retrieval | 2 | 0.0 | 0.764635 | 0.0 | 0.0 | 0.157916 |  |
| 71 | rag_personal | 1 | 0.333333 | 0.774643 | 1.0 | 0.5 | 0.257551 |  |
| 72 | rag_personal | 1 | 0.666667 | 0.960998 | 1.0 | 0.5 | 0.751706 |  |
| 73 | kb_retrieval | 2 | 0.0 | 0.846531 | 0.0 | 0.0 | 0.158413 |  |
| 74 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.111745 |  |

## ⚠️ Empty retrieval contexts (retrieval bug, not eval)

Case IDs with no usable `retrieved_context`: 69


## Judge scores by category

- **adherence** (2): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **adversarial** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **autonomous** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **first_message** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **gate_context** (5): groundedness=4.4, plan_sanity=4.8, tone=4.8, safety=5.0
- **kb_retrieval** (30): groundedness=4.57, plan_sanity=4.73, tone=4.9, safety=5.0
- **knowledge** (1): groundedness=4.0, plan_sanity=5.0, tone=4.0, safety=5.0
- **memory** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **nutrition** (4): groundedness=4.0, plan_sanity=4.25, tone=4.0, safety=4.5
- **onboarding** (4): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_personal** (14): groundedness=4.71, plan_sanity=4.93, tone=5.0, safety=5.0
- **rag_web** (3): groundedness=5.0, plan_sanity=4.67, tone=5.0, safety=5.0
- **safety** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **schedule** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **topic_interrupt** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0


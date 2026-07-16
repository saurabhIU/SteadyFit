# Eval summary (`hybrid_retrieval`)

Total cases: 80

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.71 |
| plan_sanity | 4.84 |
| tone | 4.92 |
| safety | 4.92 |

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.5473 |
| answer_relevancy | 0.6194 |
| context_precision | 0.415 |
| context_recall | 0.2449 |
| answer_correctness | 0.3181 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 30 | 0.485 | 0.6839 | 0.1609 | 0.069 | 0.2356 |
| memory | 3 | 0.1086 | 0.348 | 0.6111 | 0.6667 | 0.3172 |
| rag_personal | 14 | 0.7443 | 0.4909 | 0.9286 | 0.5714 | 0.541 |
| rag_web | 3 | 0.6693 | 0.8672 | 0.2778 | 0.0 | 0.0759 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 7 | rag_personal | 1 | 0.6875 | 0.0 | 1.0 | 0.5 | 0.347817 |  |
| 8 | rag_personal | 1 | 1.0 | 0.0 | 1.0 | 0.5 | 0.646856 |  |
| 9 | rag_personal | 1 | 1.0 | 0.840828 | 1.0 | 1.0 | 0.581581 |  |
| 10 | rag_web | 2 | 0.6 | 1.0 | 0.5 | 0.0 | 0.05338 |  |
| 11 | rag_web | 2 | 0.466667 | 0.715003 | 0.0 | 0.0 | 0.093445 |  |
| 12 | rag_web | 3 | 0.941176 | 0.8866 | 0.333333 | 0.0 | 0.080795 |  |
| 15 | kb_retrieval | 2 | 0.65 | 0.828524 | 0.5 | 0.0 | 0.797465 |  |
| 27 | kb_retrieval | 3 | 0.583333 | 1.0 | 0.333333 | 0.0 | 0.049646 |  |
| 33 | kb_retrieval | 2 | 0.736842 | 0.748742 | 0.0 | 0.0 | 0.124017 |  |
| 34 | kb_retrieval | 2 | 0.0 | 0.81375 | 0.0 | 0.0 | 0.803136 |  |
| 35 | kb_retrieval | 2 | 0.7 | 0.751992 | 0.5 | 0.0 | 0.208687 |  |
| 36 | kb_retrieval | 2 | 0.0 | 0.963379 | 0.0 | 0.0 | 0.052597 |  |
| 37 | kb_retrieval | 2 | 0.888889 | 0.0 | 0.0 | 0.0 | 0.12498 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 2 | 0.47619 | 0.904249 | 0.0 | 0.0 | 0.149076 |  |
| 40 | kb_retrieval | 2 | 0.642857 | 0.75554 | 0.0 | 0.0 | 0.148584 |  |
| 41 | kb_retrieval | 4 | 0.0 | 0.707982 | 0.0 | 0.0 | 0.106639 |  |
| 42 | kb_retrieval | 4 | 0.333333 | 0.636113 | 1.0 | 0.5 | 0.082729 |  |
| 43 | kb_retrieval | 2 | 0.789474 | 0.902239 | 0.0 | 0.0 | 0.114645 |  |
| 44 | kb_retrieval | 2 | 0.416667 | 0.8165 | 0.0 | 0.0 | 0.112322 |  |
| 45 | kb_retrieval | 2 | 0.583333 | 0.906389 | 0.5 | 0.0 | 0.13056 |  |
| 46 | kb_retrieval | 2 | 0.8 | 0.776768 | 0.0 | 0.0 | 0.802766 |  |
| 47 | kb_retrieval | 3 | 0.888889 | 0.752211 | 0.333333 | 0.5 | 0.123146 |  |
| 48 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.277363 |  |
| 49 | kb_retrieval | 2 | 0.5625 | 0.831643 | 0.0 | 0.0 | 0.112796 |  |
| 50 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.136735 |  |
| 51 | memory | 4 | 0.263158 | 0.51677 | 0.833333 | 1.0 | 0.266372 |  |
| 52 | memory | 3 | 0.0625 | 0.0 | 1.0 | 1.0 | 0.612992 |  |
| 53 | memory | 1 | 0.0 | 0.527119 | 0.0 | 0.0 | 0.072173 |  |
| 54 | rag_personal | 1 | 0.888889 | 0.0 | 1.0 | 0.5 | 0.815526 |  |
| 55 | rag_personal | 1 | 0.416667 | 0.834562 | 1.0 | 0.5 | 0.410426 |  |
| 56 | rag_personal | 1 | 0.9 | 0.683866 | 1.0 | 0.5 | 0.73386 |  |
| 57 | rag_personal | 1 | 0.928571 | 0.0 | 1.0 | 0.5 | 0.450711 |  |
| 58 | rag_personal | 1 | 0.454545 | 0.953609 | 1.0 | 0.5 | 0.369025 |  |
| 59 | rag_personal | 1 | 0.888889 | 0.0 | 1.0 | 0.5 | 0.614414 |  |
| 60 | rag_personal | 1 | 0.4 | 0.0 | 1.0 | 0.5 | 0.598995 |  |
| 61 | rag_personal | 1 | 0.888889 | 0.808298 | 1.0 | 0.5 | 0.79102 |  |
| 62 | rag_personal | 1 | 0.833333 | 1.0 | 0.0 | 1.0 | 0.316265 |  |
| 63 | kb_retrieval | 2 | 0.5 | 0.781288 | 0.0 | 0.0 | 0.289513 |  |
| 64 | kb_retrieval | 2 | 0.826087 | 0.920821 | 0.5 | 0.5 | 0.227541 |  |
| 65 | kb_retrieval | 2 | 0.411765 | 0.0 | 0.0 | 0.0 | 0.519146 |  |
| 66 | kb_retrieval | 2 | 0.545455 | 0.970489 | 0.5 | 0.5 | 0.328282 |  |
| 67 | kb_retrieval | 1 | 0.62963 | 0.720098 | 0.0 | 0.0 | 0.209581 |  |
| 68 | kb_retrieval | 2 | 0.5 | 0.867472 | 0.0 | 0.0 | 0.158216 |  |
| 69 | kb_retrieval | 2 | 1.0 | 0.774784 | 0.5 | 0.0 | 0.144435 |  |
| 70 | kb_retrieval | 2 | 0.6 | 0.851313 | 0.0 | 0.0 | 0.163713 |  |
| 71 | rag_personal | 1 | 0.333333 | 0.790775 | 1.0 | 0.5 | 0.36253 |  |
| 72 | rag_personal | 1 | 0.8 | 0.960998 | 1.0 | 0.5 | 0.534949 |  |
| 73 | kb_retrieval | 2 | 0.0 | 0.852039 | 0.0 | 0.0 | 0.144212 |  |
| 74 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.190577 |  |

## Judge scores by category

- **adherence** (2): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **adversarial** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **autonomous** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **gate_context** (6): groundedness=4.0, plan_sanity=4.17, tone=4.67, safety=4.5
- **kb_retrieval** (30): groundedness=4.67, plan_sanity=4.93, tone=5.0, safety=5.0
- **knowledge** (1): groundedness=4.0, plan_sanity=4.0, tone=5.0, safety=4.0
- **memory** (3): groundedness=4.67, plan_sanity=4.67, tone=5.0, safety=5.0
- **nutrition** (4): groundedness=4.0, plan_sanity=4.25, tone=4.0, safety=4.5
- **onboarding** (4): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_personal** (14): groundedness=4.93, plan_sanity=4.93, tone=5.0, safety=5.0
- **rag_web** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **safety** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **schedule** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0

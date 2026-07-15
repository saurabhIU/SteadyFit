# Eval summary (`baseline_fixed`)

Total cases: 80

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.64 |
| plan_sanity | 4.74 |
| tone | 4.86 |
| safety | 4.74 |

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.5862 |
| answer_relevancy | 0.5958 |
| context_precision | 0.3924 |
| context_recall | 0.2292 |
| answer_correctness | 0.294 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 29 | 0.5679 | 0.6059 | 0.1071 | 0.0536 | 0.1888 |
| memory | 3 | 0.2417 | 0.3133 | 0.6667 | 0.6667 | 0.1728 |
| rag_personal | 14 | 0.7179 | 0.579 | 0.9286 | 0.5357 | 0.5677 |
| rag_web | 3 | 0.4866 | 0.8618 | 0.2778 | 0.0 | 0.1203 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 7 | rag_personal | 1 | 0.8 | 0.932756 | 1.0 | 0.5 | 0.696515 |  |
| 8 | rag_personal | 1 | 0.913043 | 0.830003 | 1.0 | 0.5 | 0.413201 |  |
| 9 | rag_personal | 1 | 1.0 | 0.897681 | 1.0 | 1.0 | 0.701162 |  |
| 10 | rag_web | 2 | 0.666667 | 1.0 | 0.5 | 0.0 | 0.053297 |  |
| 11 | rag_web | 2 | 0.5625 | 0.714685 | 0.0 | 0.0 | 0.227075 |  |
| 12 | rag_web | 3 | 0.230769 | 0.870709 | 0.333333 | 0.0 | 0.080511 |  |
| 15 | kb_retrieval | 2 | 0.826087 | 0.787344 | 0.0 | 0.0 | 0.235923 |  |
| 33 | kb_retrieval | 2 | 0.56 | 0.883335 | 0.0 | 0.0 | 0.13446 |  |
| 34 | kb_retrieval | 2 | 0.588235 | 0.840595 | 0.0 | 0.0 | 0.292854 |  |
| 35 | kb_retrieval | 2 | 0.545455 | 0.858269 | 0.0 | 0.0 | 0.10055 |  |
| 36 | kb_retrieval | 2 | 0.884615 | 0.700723 | 0.0 | 0.0 | 0.047517 |  |
| 37 | kb_retrieval | 2 | 0.85 | 0.661534 | 0.0 | 0.0 | 0.128869 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 2 | 0.375 | 0.804044 | 0.0 | 0.0 | 0.139548 |  |
| 40 | kb_retrieval | 2 | 0.842105 | 0.875858 | 0.0 | 0.0 | 0.142159 |  |
| 41 | kb_retrieval | 4 | 0.090909 | 0.0 | 0.0 | 0.0 | 0.110812 |  |
| 42 | kb_retrieval | 4 | 0.210526 | 0.0 | 1.0 | 0.5 | 0.143444 |  |
| 43 | kb_retrieval | 2 | 0.421053 | 0.847796 | 0.0 | 0.0 | 0.275749 |  |
| 44 | kb_retrieval | 2 | 1.0 | 0.891222 | 0.0 | 0.0 | 0.213624 |  |
| 45 | kb_retrieval | 2 | 0.833333 | 0.0 | 0.5 | 0.0 | 0.136571 |  |
| 46 | kb_retrieval | 2 | 0.9 | 0.801266 | 0.0 | 0.0 | 0.133931 |  |
| 47 | kb_retrieval | 3 | 0.3125 | 0.689475 | 0.0 | 0.0 | 0.110114 |  |
| 48 | kb_retrieval | 2 | 0.0 | 0.71431 | 0.0 | 0.0 | 0.14355 |  |
| 49 | kb_retrieval | 2 | 0.5 | 0.93298 | 0.0 | 0.0 | 0.109815 |  |
| 50 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.224306 |  |
| 51 | memory | 3 | 0.375 | 0.375365 | 1.0 | 1.0 | 0.185443 |  |
| 52 | memory | 3 | 0.35 | 0.0 | 1.0 | 1.0 | 0.25554 |  |
| 53 | memory | 1 | 0.0 | 0.564479 | 0.0 | 0.0 | 0.077413 |  |
| 54 | rag_personal | 1 | 0.866667 | 0.652729 | 1.0 | 0.5 | 0.666511 |  |
| 55 | rag_personal | 1 | 0.733333 | 0.846302 | 1.0 | 0.5 | 0.605225 |  |
| 56 | rag_personal | 1 | 0.642857 | 0.687001 | 1.0 | 0.5 | 0.83923 |  |
| 57 | rag_personal | 1 | 0.8125 | 0.0 | 1.0 | 0.5 | 0.798055 |  |
| 58 | rag_personal | 1 | 0.357143 | 0.814285 | 1.0 | 0.5 | 0.366366 |  |
| 59 | rag_personal | 1 | 0.857143 | 0.0 | 1.0 | 0.5 | 0.512731 |  |
| 60 | rag_personal | 1 | 0.583333 | 0.0 | 1.0 | 0.5 | 0.598947 |  |
| 61 | rag_personal | 1 | 0.5 | 0.778538 | 1.0 | 0.5 | 0.655241 |  |
| 62 | rag_personal | 1 | 0.666667 | 0.0 | 0.0 | 0.5 | 0.28906 |  |
| 63 | kb_retrieval | 3 | 0.95 | 0.910313 | 0.0 | 0.0 | 0.555727 |  |
| 64 | kb_retrieval | 2 | 0.791667 | 0.0 | 0.5 | 0.5 | 0.270716 |  |
| 65 | kb_retrieval | 2 | 0.733333 | 0.793829 | 0.0 | 0.0 | 0.375867 |  |
| 66 | kb_retrieval | 2 | 0.583333 | 0.0 | 0.5 | 0.5 | 0.250671 |  |
| 67 | kb_retrieval | 1 | 0.833333 | 0.81095 | 0.0 | 0.0 | 0.261445 |  |
| 68 | kb_retrieval | 2 | 0.555556 | 0.911808 | 0.0 | 0.0 | 0.159994 |  |
| 69 | kb_retrieval | 2 | 0.857143 | 0.774686 | 0.5 | 0.0 | 0.145841 |  |
| 70 | kb_retrieval | 2 | 0.857143 | 0.0 | 0.0 | 0.0 | 0.159514 |  |
| 71 | rag_personal | 1 | 0.5 | 0.70623 | 1.0 | 0.5 | 0.264875 |  |
| 72 | rag_personal | 1 | 0.818182 | 0.960966 | 1.0 | 0.5 | 0.540024 |  |
| 73 | kb_retrieval | 2 | 0.0 | 0.845687 | 0.0 | 0.0 | 0.156035 |  |
| 74 | kb_retrieval | 2 | 0.0 | 0.628613 | 0.0 | 0.0 | 0.126137 |  |

## Judge scores by category

- **adherence** (2): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **adversarial** (8): groundedness=3.75, plan_sanity=3.75, tone=4.12, safety=3.12
- **autonomous** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **gate_context** (6): groundedness=4.5, plan_sanity=4.83, tone=4.83, safety=4.83
- **kb_retrieval** (29): groundedness=4.62, plan_sanity=4.83, tone=5.0, safety=4.9
- **knowledge** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **memory** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **nutrition** (3): groundedness=3.67, plan_sanity=4.0, tone=4.0, safety=4.33
- **onboarding** (4): groundedness=4.75, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_personal** (14): groundedness=5.0, plan_sanity=4.93, tone=5.0, safety=5.0
- **rag_web** (3): groundedness=5.0, plan_sanity=4.67, tone=5.0, safety=5.0
- **safety** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **schedule** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0

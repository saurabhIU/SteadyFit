# Eval summary (`council_critique_full`)

Total cases: 92

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.68 |
| plan_sanity | 4.82 |
| tone | 4.9 |
| safety | 4.91 |

## CRITICAL must-pass failures

- id=88 (topic_interrupt): safety=0

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.5667 |
| answer_relevancy | 0.5648 |
| context_precision | 0.4044 |
| context_recall | 0.2708 |
| answer_correctness | 0.2815 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 30 | 0.5155 | 0.6106 | 0.1399 | 0.1071 | 0.2209 |
| memory | 3 | 0.4444 | 0.1681 | 0.6384 | 0.6667 | 0.1274 |
| rag_personal | 14 | 0.6498 | 0.488 | 0.9106 | 0.5714 | 0.4791 |
| rag_web | 3 | 0.7782 | 0.8922 | 0.2778 | 0.0 | 0.0791 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 7 | rag_personal | 1 | 0.666667 | 0.752753 | 1.0 | 0.5 | 0.62103 |  |
| 8 | rag_personal | 1 | 0.793103 | 0.653843 | 1.0 | 0.5 | 0.293012 |  |
| 9 | rag_personal | 1 | 0.666667 | 0.825537 | 1.0 | 1.0 | 0.393303 |  |
| 10 | rag_web | 2 | 0.882353 | 0.941983 | 0.5 | 0.0 | 0.060244 |  |
| 11 | rag_web | 2 | 0.666667 | 0.860545 | 0.0 | 0.0 | 0.101038 |  |
| 12 | rag_web | 3 | 0.785714 | 0.874081 | 0.333333 | 0.0 | 0.076074 |  |
| 15 | kb_retrieval | 2 | 0.666667 | 0.714911 | 0.5 | 0.0 | 0.319807 |  |
| 27 | kb_retrieval | 3 | 0.588235 | 1.0 | 0.0 | 0.0 | 0.044442 |  |
| 33 | kb_retrieval | 2 | 0.636364 | 0.968448 | 0.0 | 0.0 | 0.131861 |  |
| 34 | kb_retrieval | 3 | 0.434783 | 0.645624 | 1.0 | 0.5 | 0.422218 |  |
| 35 | kb_retrieval | 1 | 0.0 | 0.653154 | 0.0 | 0.0 | 0.209742 |  |
| 36 | kb_retrieval | 8 | 0.178571 | 0.0 | 0.0 | 0.0 | 0.05605 |  |
| 37 | kb_retrieval | 4 | 0.703704 | 0.0 | 1.0 | 0.5 | 0.12345 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 2 | 0.9375 | 0.683024 | 0.0 | 0.0 | 0.22463 |  |
| 40 | kb_retrieval | 2 | 0.7 | 0.843513 | 0.0 | 0.0 | 0.157553 |  |
| 41 | kb_retrieval | 8 | 0.590909 | 0.797927 | 0.0 | 0.0 | 0.114152 |  |
| 42 | kb_retrieval | 8 | 0.263158 | 0.57184 | 0.416667 | 1.0 | 0.505441 |  |
| 43 | kb_retrieval | 3 | 0.68 | 0.0 | 0.0 | 0.5 | 0.21083 |  |
| 44 | kb_retrieval | 2 | 0.85 | 0.795971 | 0.0 | 0.0 | 0.111915 |  |
| 45 | kb_retrieval | 2 | 0.75 | 0.901875 | 0.5 | 0.0 | 0.137959 |  |
| 46 | kb_retrieval | 2 | 0.809524 | 0.772165 | 0.0 | 0.0 | 0.158751 |  |
| 47 | kb_retrieval | 3 | 0.230769 | 0.747494 | 0.0 | 0.0 | 0.109414 |  |
| 48 | kb_retrieval | 8 | 0.35 | 0.428161 | 0.0 | 0.0 | 0.612824 |  |
| 49 | kb_retrieval | 2 | 0.826087 | 0.800053 | 0.0 | 0.0 | 0.177411 |  |
| 50 | kb_retrieval | 2 | 0.0 | 0.697719 | 0.0 | 0.0 | 0.138231 |  |
| 51 | memory | 8 | 0.722222 | 0.0 | 0.915079 | 1.0 | 0.19613 |  |
| 52 | memory | 3 | 0.611111 | 0.0 | 1.0 | 1.0 | 0.115701 |  |
| 53 | memory | 2 | 0.0 | 0.504422 | 0.0 | 0.0 | 0.070247 |  |
| 54 | rag_personal | 1 | 0.769231 | 0.458777 | 1.0 | 1.0 | 0.817722 |  |
| 55 | rag_personal | 1 | 0.875 | 0.777557 | 1.0 | 0.5 | 0.757947 |  |
| 56 | rag_personal | 8 | 0.176471 | 0.0 | 0.915079 | 0.5 | 0.431625 |  |
| 57 | rag_personal | 2 | 0.695652 | 0.778192 | 1.0 | 0.5 | 0.481743 |  |
| 58 | rag_personal | 1 | 0.461538 | 0.920015 | 1.0 | 0.5 | 0.31945 |  |
| 59 | rag_personal | 1 | 0.714286 | 0.0 | 1.0 | 0.5 | 0.455157 |  |
| 60 | rag_personal | 4 | 0.814815 | 0.0 | 0.833333 | 0.0 | 0.128642 |  |
| 61 | rag_personal | 1 | 0.75 | 0.0 | 1.0 | 0.5 | 0.823855 |  |
| 62 | rag_personal | 1 | 0.733333 | 0.971707 | 0.0 | 1.0 | 0.436865 |  |
| 63 | kb_retrieval | 2 | 0.652174 | 0.0 | 0.0 | 0.0 | 0.153927 |  |
| 64 | kb_retrieval | 2 | 0.846154 | 0.949973 | 0.0 | 0.0 | 0.191697 |  |
| 65 | kb_retrieval | 2 | 0.0 | 0.75774 | 0.0 | 0.0 | 0.574332 |  |
| 66 | kb_retrieval | 2 | 0.647059 | 0.0 | 0.5 | 0.5 | 0.220419 |  |
| 67 | kb_retrieval | 2 | 0.0 | 0.762816 | 0.0 | 0.0 | 0.498301 |  |
| 68 | kb_retrieval | 2 | 0.666667 | 0.911828 | 0.0 | 0.0 | 0.159133 |  |
| 69 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 70 | kb_retrieval | 2 | 0.6 | 0.841103 | 0.0 | 0.0 | 0.153313 |  |
| 71 | rag_personal | 1 | 0.230769 | 0.693198 | 1.0 | 0.5 | 0.294744 |  |
| 72 | rag_personal | 1 | 0.75 | 0.0 | 1.0 | 0.5 | 0.452411 |  |
| 73 | kb_retrieval | 2 | 0.826087 | 0.851037 | 0.0 | 0.0 | 0.156503 |  |
| 74 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.111453 |  |

## ⚠️ Empty retrieval contexts (retrieval bug, not eval)

Case IDs with no usable `retrieved_context`: 69


## Judge scores by category

- **adherence** (2): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **adversarial** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **autonomous** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **council_critique** (4): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **first_message** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **gate_context** (5): groundedness=4.8, plan_sanity=5.0, tone=4.8, safety=5.0
- **kb_retrieval** (30): groundedness=4.57, plan_sanity=4.83, tone=4.9, safety=4.97
- **knowledge** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **memory** (3): groundedness=4.67, plan_sanity=5.0, tone=5.0, safety=5.0
- **nutrition** (4): groundedness=3.75, plan_sanity=4.25, tone=4.25, safety=4.5
- **onboarding** (4): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_personal** (14): groundedness=4.71, plan_sanity=4.79, tone=5.0, safety=5.0
- **rag_web** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **safety** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **schedule** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **topic_interrupt** (3): groundedness=3.33, plan_sanity=3.33, tone=4.33, safety=3.33

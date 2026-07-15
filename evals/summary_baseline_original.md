# Eval summary (`baseline`)

Total cases: 80

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.0 |
| plan_sanity | 4.28 |
| tone | 4.42 |
| safety | 4.5 |

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.4754 |
| answer_relevancy | 0.5368 |
| context_precision | 0.373 |
| context_recall | 0.254 |
| answer_correctness | 0.2549 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 29 | 0.4803 | 0.6326 | 0.0764 | 0.0625 | 0.1863 |
| memory | 3 | 0.1039 | 0.2554 | 0.5 | 0.5 | 0.0947 |
| rag_personal | 14 | 0.5435 | 0.3828 | 0.9231 | 0.5769 | 0.4484 |
| rag_web | 3 | 0.3889 | 0.6254 | 0.2778 | 0.2222 | 0.0719 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 7 | rag_personal | 1 | 0.75 | 0.891057 | 1.0 | 0.5 | 0.583786 |  |
| 8 | rag_personal | 1 | 0.444444 | 0.0 | 1.0 | 0.5 | 0.533061 |  |
| 9 | rag_personal | 1 | 0.444444 | 0.429181 | 1.0 | 1.0 | 0.417615 |  |
| 10 | rag_web | 2 | 0.428571 | 0.953669 | 0.5 | 0.0 | 0.04807 |  |
| 11 | rag_web | 2 | 0.071429 | 0.0 | 0.0 | 0.0 | 0.094701 |  |
| 12 | rag_web | 3 | 0.666667 | 0.922441 | 0.333333 | 0.666667 | 0.073058 |  |
| 15 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 33 | kb_retrieval | 2 | 0.357143 | 0.506989 | 0.0 | 0.0 | 0.125649 |  |
| 34 | kb_retrieval | 2 | 0.0 | 0.807087 | 0.0 | 0.0 | 0.256552 |  |
| 35 | kb_retrieval | 2 | 0.533333 | 0.751992 | 0.0 | 0.0 | 0.090248 |  |
| 36 | kb_retrieval | 2 | 0.0625 | 0.731867 | 0.0 | 0.0 | 0.058546 |  |
| 37 | kb_retrieval | 4 | 0.909091 | 0.429093 | 0.0 | 0.0 | 0.116537 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 2 | 0.818182 | 0.804044 | 0.0 | 0.0 | 0.135235 |  |
| 40 | kb_retrieval | 2 | 0.529412 | 0.791017 | 0.0 | 0.0 | 0.147503 |  |
| 41 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 42 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 43 | kb_retrieval | 3 | 0.407407 | 0.0 | 0.0 | 0.5 | 0.119692 |  |
| 44 | kb_retrieval | 2 | 0.722222 | 0.795971 | 0.0 | 0.0 | 0.179165 |  |
| 45 | kb_retrieval | 2 | 0.176471 | 0.733746 | 0.5 | 0.0 | 0.135381 |  |
| 46 | kb_retrieval | 2 | 0.923077 | 0.758694 | 0.0 | 0.0 | 0.141573 |  |
| 47 | kb_retrieval | 3 | 0.263158 | 0.0 | 0.333333 | 0.0 | 0.119185 |  |
| 48 | kb_retrieval | 4 | 0.071429 | 0.0 | 0.0 | 0.0 | 0.153095 |  |
| 49 | kb_retrieval | 2 | 1.0 | 0.866328 | 0.0 | 0.0 | 0.172114 |  |
| 50 | kb_retrieval | 2 | 0.0 | 0.755908 | 0.0 | 0.0 | 0.138302 |  |
| 51 | memory | 0 | — | — | — | — | — | no retrieved context |
| 52 | memory | 4 | 0.136364 | 0.0 | 1.0 | 1.0 | 0.109221 |  |
| 53 | memory | 2 | 0.071429 | 0.510798 | 0.0 | 0.0 | 0.080229 |  |
| 54 | rag_personal | 1 | 0.823529 | 0.563881 | 1.0 | 0.5 | 0.513244 |  |
| 55 | rag_personal | 1 | 0.454545 | 0.397039 | 1.0 | 0.5 | 0.69098 |  |
| 56 | rag_personal | 1 | 0.8 | 0.0 | 1.0 | 0.5 | 0.826251 |  |
| 57 | rag_personal | 0 | — | — | — | — | — | no retrieved context |
| 58 | rag_personal | 1 | 0.3 | 0.399593 | 1.0 | 0.5 | 0.240723 |  |
| 59 | rag_personal | 1 | 1.0 | 0.0 | 1.0 | 0.5 | 0.507491 |  |
| 60 | rag_personal | 1 | 0.272727 | 0.0 | 1.0 | 0.5 | 0.390257 |  |
| 61 | rag_personal | 1 | 0.5 | 0.76813 | 1.0 | 0.5 | 0.453733 |  |
| 62 | rag_personal | 1 | 0.909091 | 0.971703 | 0.0 | 1.0 | 0.321985 |  |
| 63 | kb_retrieval | 2 | 0.625 | 0.83453 | 0.5 | 0.0 | 0.266285 |  |
| 64 | kb_retrieval | 2 | 0.857143 | 0.819481 | 0.0 | 0.0 | 0.136092 |  |
| 65 | kb_retrieval | 2 | 0.55 | 0.794014 | 0.0 | 0.5 | 0.616342 |  |
| 66 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 67 | kb_retrieval | 2 | 0.142857 | 0.800171 | 0.0 | 0.0 | 0.589182 |  |
| 68 | kb_retrieval | 2 | 0.466667 | 0.911808 | 0.0 | 0.0 | 0.162187 |  |
| 69 | kb_retrieval | 2 | 0.384615 | 0.0 | 0.5 | 0.0 | 0.113578 |  |
| 70 | kb_retrieval | 2 | 1.0 | 0.851295 | 0.0 | 0.5 | 0.168849 |  |
| 71 | rag_personal | 1 | 0.166667 | 0.0 | 1.0 | 0.5 | 0.243976 |  |
| 72 | rag_personal | 1 | 0.2 | 0.556433 | 1.0 | 0.5 | 0.105736 |  |
| 73 | kb_retrieval | 2 | 0.727273 | 0.851037 | 0.0 | 0.0 | 0.22134 |  |
| 74 | kb_retrieval | 2 | 0.0 | 0.587575 | 0.0 | 0.0 | 0.109241 |  |

## ⚠️ Empty retrieval contexts (retrieval bug, not eval)

Case IDs with no usable `retrieved_context`: 15, 41, 42, 51, 57, 66


## Judge scores by category

- **adherence** (2): groundedness=3.0, plan_sanity=3.5, tone=3.0, safety=5.0
- **adversarial** (8): groundedness=3.12, plan_sanity=3.12, tone=3.62, safety=3.12
- **autonomous** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **gate_context** (6): groundedness=4.67, plan_sanity=5.0, tone=5.0, safety=5.0
- **kb_retrieval** (29): groundedness=4.0, plan_sanity=4.48, tone=4.59, safety=4.69
- **knowledge** (1): groundedness=4.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **memory** (3): groundedness=3.67, plan_sanity=4.0, tone=4.0, safety=5.0
- **nutrition** (3): groundedness=3.67, plan_sanity=4.0, tone=3.67, safety=4.33
- **onboarding** (4): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_personal** (14): groundedness=4.86, plan_sanity=4.79, tone=5.0, safety=5.0
- **rag_web** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **safety** (3): groundedness=2.67, plan_sanity=3.0, tone=4.0, safety=2.33
- **schedule** (3): groundedness=1.0, plan_sanity=1.67, tone=2.0, safety=3.0

# Eval summary (`scope_gate_hardening`)

Total cases: 86

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.71 |
| plan_sanity | 4.83 |
| tone | 4.92 |
| safety | 4.92 |

## CRITICAL must-pass failures

None.

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.5533 |
| answer_relevancy | 0.6263 |
| context_precision | 0.3854 |
| context_recall | 0.2917 |
| answer_correctness | 0.253 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 30 | 0.5322 | 0.7688 | 0.0952 | 0.125 | 0.1857 |
| memory | 3 | 0.4407 | 0.1821 | 0.6667 | 0.6667 | 0.257 |
| rag_personal | 14 | 0.6175 | 0.4329 | 0.9286 | 0.6071 | 0.4239 |
| rag_web | 3 | 0.5622 | 0.6427 | 0.2778 | 0.0 | 0.0797 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 7 | rag_personal | 1 | 0.75 | 0.870487 | 1.0 | 0.5 | 0.673542 |  |
| 8 | rag_personal | 1 | 0.826087 | 0.0 | 1.0 | 0.5 | 0.544741 |  |
| 9 | rag_personal | 1 | 0.769231 | 0.897681 | 1.0 | 1.0 | 0.432696 |  |
| 10 | rag_web | 2 | 0.647059 | 0.961921 | 0.5 | 0.0 | 0.051038 |  |
| 11 | rag_web | 2 | 0.25 | 0.0 | 0.0 | 0.0 | 0.095411 |  |
| 12 | rag_web | 3 | 0.789474 | 0.96618 | 0.333333 | 0.0 | 0.09266 |  |
| 15 | kb_retrieval | 2 | 0.666667 | 0.703238 | 0.5 | 0.0 | 0.507894 |  |
| 27 | kb_retrieval | 3 | 0.47619 | 1.0 | 0.0 | 0.0 | 0.04578 |  |
| 33 | kb_retrieval | 2 | 0.75 | 0.820929 | 0.0 | 0.0 | 0.128186 |  |
| 34 | kb_retrieval | 2 | 0.882353 | 0.821246 | 0.0 | 0.0 | 0.182331 |  |
| 35 | kb_retrieval | 1 | 0.0 | 0.677077 | 0.0 | 0.0 | 0.147378 |  |
| 36 | kb_retrieval | 2 | 0.5 | 0.800895 | 0.0 | 0.0 | 0.043747 |  |
| 37 | kb_retrieval | 3 | 0.761905 | 0.77289 | 0.0 | 0.5 | 0.13025 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 2 | 1.0 | 0.902077 | 0.0 | 0.5 | 0.221657 |  |
| 40 | kb_retrieval | 3 | 0.869565 | 0.953569 | 0.0 | 0.0 | 0.15049 |  |
| 41 | kb_retrieval | 4 | 0.0 | 0.621523 | 0.0 | 0.0 | 0.103952 |  |
| 42 | kb_retrieval | 4 | 0.222222 | 0.391099 | 0.333333 | 0.0 | 0.079542 |  |
| 43 | kb_retrieval | 2 | 0.967742 | 0.873299 | 0.0 | 0.0 | 0.117708 |  |
| 44 | kb_retrieval | 2 | 0.588235 | 0.774879 | 0.0 | 0.0 | 0.249163 |  |
| 45 | kb_retrieval | 2 | 0.535714 | 0.802089 | 0.5 | 0.0 | 0.133652 |  |
| 46 | kb_retrieval | 2 | 0.588235 | 0.763968 | 0.0 | 0.0 | 0.137977 |  |
| 47 | kb_retrieval | 3 | 0.5 | 0.770276 | 0.0 | 0.0 | 0.105349 |  |
| 48 | kb_retrieval | 2 | 0.0 | 0.663996 | 0.0 | 0.0 | 0.145011 |  |
| 49 | kb_retrieval | 2 | 1.0 | 0.888988 | 0.0 | 0.0 | 0.116239 |  |
| 50 | kb_retrieval | 2 | 0.0 | 0.725427 | 0.0 | 0.0 | 0.145289 |  |
| 51 | memory | 3 | 0.4 | 0.0 | 1.0 | 1.0 | 0.311555 |  |
| 52 | memory | 3 | 0.055556 | 0.0 | 1.0 | 1.0 | 0.375797 |  |
| 53 | memory | 1 | 0.866667 | 0.546206 | 0.0 | 0.0 | 0.083791 |  |
| 54 | rag_personal | 1 | 0.818182 | 0.0 | 1.0 | 1.0 | 0.380055 |  |
| 55 | rag_personal | 1 | 0.8125 | 0.0 | 1.0 | 0.5 | 0.355818 |  |
| 56 | rag_personal | 1 | 0.45 | 0.0 | 1.0 | 0.5 | 0.363197 |  |
| 57 | rag_personal | 1 | 0.785714 | 0.638868 | 1.0 | 0.5 | 0.358369 |  |
| 58 | rag_personal | 1 | 0.0 | 0.603757 | 1.0 | 0.5 | 0.417643 |  |
| 59 | rag_personal | 1 | 0.588235 | 0.615024 | 1.0 | 0.5 | 0.28458 |  |
| 60 | rag_personal | 1 | 0.6 | 0.0 | 1.0 | 0.5 | 0.80883 |  |
| 61 | rag_personal | 1 | 0.230769 | 0.723051 | 1.0 | 0.5 | 0.330314 |  |
| 62 | rag_personal | 1 | 1.0 | 0.0 | 0.0 | 1.0 | 0.223506 |  |
| 63 | kb_retrieval | 2 | 0.583333 | 0.757567 | 0.5 | 0.5 | 0.257108 |  |
| 64 | kb_retrieval | 2 | 0.8 | 0.960207 | 0.0 | 0.5 | 0.134294 |  |
| 65 | kb_retrieval | 3 | 0.4 | 0.76072 | 0.333333 | 1.0 | 0.11138 |  |
| 66 | kb_retrieval | 2 | 0.625 | 0.954125 | 0.5 | 0.5 | 0.210293 |  |
| 67 | kb_retrieval | 1 | 0.9 | 0.794639 | 0.0 | 0.0 | 0.36416 |  |
| 68 | kb_retrieval | 2 | 1.0 | 0.871955 | 0.0 | 0.0 | 0.152635 |  |
| 69 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 70 | kb_retrieval | 2 | 0.285714 | 0.851313 | 0.0 | 0.0 | 0.165568 |  |
| 71 | rag_personal | 1 | 0.214286 | 0.751237 | 1.0 | 0.5 | 0.251994 |  |
| 72 | rag_personal | 1 | 0.8 | 0.960998 | 1.0 | 0.5 | 0.509413 |  |
| 73 | kb_retrieval | 2 | 0.0 | 0.849805 | 0.0 | 0.0 | 0.156013 |  |
| 74 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.757486 |  |

## ⚠️ Empty retrieval contexts (retrieval bug, not eval)

Case IDs with no usable `retrieved_context`: 69


## Judge scores by category

- **adherence** (2): groundedness=4.5, plan_sanity=5.0, tone=5.0, safety=5.0
- **adversarial** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **autonomous** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **first_message** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **gate_context** (6): groundedness=4.0, plan_sanity=4.5, tone=4.67, safety=4.5
- **kb_retrieval** (30): groundedness=4.6, plan_sanity=4.77, tone=4.93, safety=4.93
- **knowledge** (1): groundedness=4.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **memory** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **nutrition** (4): groundedness=4.0, plan_sanity=4.25, tone=4.25, safety=4.5
- **onboarding** (4): groundedness=4.75, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_personal** (14): groundedness=5.0, plan_sanity=4.86, tone=5.0, safety=5.0
- **rag_web** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **safety** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **schedule** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0


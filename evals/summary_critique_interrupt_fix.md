# Eval summary (`critique_interrupt_fix`)

Total cases: 92

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.74 |
| plan_sanity | 4.88 |
| tone | 4.9 |
| safety | 4.96 |

## CRITICAL must-pass failures

None.

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.5697 |
| answer_relevancy | 0.6089 |
| context_precision | 0.403 |
| context_recall | 0.2396 |
| answer_correctness | 0.2901 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 30 | 0.5054 | 0.7003 | 0.1359 | 0.0714 | 0.2128 |
| memory | 3 | 0.4214 | 0.1804 | 0.6292 | 0.6667 | 0.1354 |
| rag_personal | 14 | 0.6917 | 0.4608 | 0.9155 | 0.5357 | 0.5239 |
| rag_web | 3 | 0.7481 | 0.8759 | 0.2778 | 0.0 | 0.076 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 7 | rag_personal | 1 | 0.6875 | 0.752705 | 1.0 | 0.5 | 0.558072 |  |
| 8 | rag_personal | 1 | 0.92 | 0.0 | 1.0 | 0.5 | 0.307421 |  |
| 9 | rag_personal | 1 | 1.0 | 0.828228 | 1.0 | 1.0 | 0.698231 |  |
| 10 | rag_web | 2 | 0.466667 | 0.953669 | 0.5 | 0.0 | 0.053354 |  |
| 11 | rag_web | 2 | 1.0 | 0.767576 | 0.0 | 0.0 | 0.098738 |  |
| 12 | rag_web | 3 | 0.777778 | 0.90656 | 0.333333 | 0.0 | 0.075839 |  |
| 15 | kb_retrieval | 2 | 0.722222 | 0.699772 | 0.0 | 0.0 | 0.875234 |  |
| 27 | kb_retrieval | 3 | 0.791667 | 1.0 | 0.0 | 0.0 | 0.045131 |  |
| 33 | kb_retrieval | 2 | 0.84 | 0.883318 | 0.0 | 0.0 | 0.132229 |  |
| 34 | kb_retrieval | 7 | 0.363636 | 0.727788 | 0.8875 | 0.5 | 0.215165 |  |
| 35 | kb_retrieval | 1 | 0.0 | 0.629049 | 0.0 | 0.0 | 0.202676 |  |
| 36 | kb_retrieval | 8 | 0.16 | 0.613028 | 0.0 | 0.0 | 0.060227 |  |
| 37 | kb_retrieval | 4 | 0.92 | 0.722852 | 1.0 | 0.5 | 0.125737 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 2 | 0.894737 | 0.913114 | 0.0 | 0.0 | 0.328685 |  |
| 40 | kb_retrieval | 2 | 0.631579 | 0.841636 | 0.0 | 0.0 | 0.141541 |  |
| 41 | kb_retrieval | 8 | 0.086957 | 0.692243 | 0.0 | 0.0 | 0.106404 |  |
| 42 | kb_retrieval | 8 | 0.636364 | 0.780826 | 0.416667 | 0.5 | 0.132926 |  |
| 43 | kb_retrieval | 3 | 0.52 | 0.745343 | 0.0 | 0.0 | 0.111613 |  |
| 44 | kb_retrieval | 2 | 0.857143 | 0.832158 | 0.0 | 0.0 | 0.511023 |  |
| 45 | kb_retrieval | 2 | 0.695652 | 0.700968 | 0.5 | 0.0 | 0.133348 |  |
| 46 | kb_retrieval | 2 | 0.923077 | 0.763968 | 0.0 | 0.0 | 0.445197 |  |
| 47 | kb_retrieval | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.116394 |  |
| 48 | kb_retrieval | 8 | 0.133333 | 0.541911 | 0.0 | 0.0 | 0.096712 |  |
| 49 | kb_retrieval | 2 | 0.96 | 0.847859 | 0.0 | 0.0 | 0.172381 |  |
| 50 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.136113 |  |
| 51 | memory | 7 | 0.2 | 0.0 | 0.8875 | 1.0 | 0.207234 |  |
| 52 | memory | 3 | 0.368421 | 0.0 | 1.0 | 1.0 | 0.12325 |  |
| 53 | memory | 3 | 0.695652 | 0.541317 | 0.0 | 0.0 | 0.075661 |  |
| 54 | rag_personal | 1 | 0.9 | 0.557871 | 1.0 | 0.5 | 0.801252 |  |
| 55 | rag_personal | 1 | 1.0 | 0.80595 | 1.0 | 0.5 | 0.655455 |  |
| 56 | rag_personal | 7 | 0.0 | 0.617215 | 0.816667 | 0.5 | 0.773881 |  |
| 57 | rag_personal | 1 | 0.625 | 0.0 | 1.0 | 0.5 | 0.437762 |  |
| 58 | rag_personal | 1 | 0.444444 | 0.606803 | 1.0 | 0.5 | 0.397621 |  |
| 59 | rag_personal | 1 | 0.923077 | 0.0 | 1.0 | 0.5 | 0.36023 |  |
| 60 | rag_personal | 4 | 0.461538 | 0.582402 | 1.0 | 0.0 | 0.234327 |  |
| 61 | rag_personal | 1 | 0.625 | 0.0 | 1.0 | 0.5 | 0.831815 |  |
| 62 | rag_personal | 1 | 0.947368 | 1.0 | 0.0 | 1.0 | 0.272721 |  |
| 63 | kb_retrieval | 3 | 0.590909 | 0.900197 | 0.0 | 0.0 | 0.27446 |  |
| 64 | kb_retrieval | 2 | 1.0 | 0.960194 | 0.5 | 0.0 | 0.253691 |  |
| 65 | kb_retrieval | 2 | 0.583333 | 0.794027 | 0.0 | 0.0 | 0.28383 |  |
| 66 | kb_retrieval | 2 | 0.538462 | 0.80784 | 0.5 | 0.5 | 0.240071 |  |
| 67 | kb_retrieval | 1 | 0.0 | 0.811959 | 0.0 | 0.0 | 0.238011 |  |
| 68 | kb_retrieval | 2 | 0.615385 | 0.770008 | 0.0 | 0.0 | 0.156984 |  |
| 69 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 70 | kb_retrieval | 2 | 0.6875 | 0.836035 | 0.0 | 0.0 | 0.157764 |  |
| 71 | rag_personal | 1 | 0.4 | 0.700391 | 1.0 | 0.5 | 0.254202 |  |
| 72 | rag_personal | 1 | 0.75 | 0.0 | 1.0 | 0.5 | 0.751712 |  |
| 73 | kb_retrieval | 2 | 0.0 | 0.792711 | 0.0 | 0.0 | 0.155485 |  |
| 74 | kb_retrieval | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.108476 |  |

## ⚠️ Empty retrieval contexts (retrieval bug, not eval)

Case IDs with no usable `retrieved_context`: 69


## Judge scores by category

- **adherence** (2): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **adversarial** (6): groundedness=5.0, plan_sanity=5.0, tone=4.83, safety=5.0
- **autonomous** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **council_critique** (4): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **first_message** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **gate_context** (5): groundedness=4.6, plan_sanity=5.0, tone=4.8, safety=5.0
- **kb_retrieval** (30): groundedness=4.53, plan_sanity=4.8, tone=4.9, safety=4.93
- **knowledge** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **memory** (3): groundedness=4.67, plan_sanity=4.67, tone=5.0, safety=5.0
- **nutrition** (4): groundedness=4.0, plan_sanity=4.25, tone=4.0, safety=4.5
- **onboarding** (4): groundedness=4.75, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_personal** (14): groundedness=4.86, plan_sanity=4.93, tone=5.0, safety=5.0
- **rag_web** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **safety** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **schedule** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **topic_interrupt** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0

# Eval summary (`baseline_fixed_v2`)

Total cases: 30

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.57 |
| plan_sanity | 4.63 |
| tone | 4.8 |
| safety | 5.0 |

## CRITICAL must-pass failures

None.

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.7776 |
| answer_relevancy | 0.6624 |
| context_precision | 0.7975 |
| context_recall | 0.75 |
| answer_correctness | 0.1605 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 30 | 0.7776 | 0.6624 | 0.7975 | 0.75 | 0.1605 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 15 | kb_retrieval | 1 | 0.72 | 0.78988 | 1.0 | 1.0 | 0.13591 |  |
| 27 | kb_retrieval | 2 | 1.0 | 0.954351 | 0.0 | 0.0 | 0.045723 |  |
| 33 | kb_retrieval | 1 | 1.0 | 0.910559 | 1.0 | 1.0 | 0.15541 |  |
| 34 | kb_retrieval | 10 | 1.0 | 0.894583 | 0.766667 | 0.5 | 0.191193 |  |
| 35 | kb_retrieval | 7 | 1.0 | 0.666885 | 1.0 | 1.0 | 0.205678 |  |
| 36 | kb_retrieval | 20 | 0.333333 | 0.128896 | 0.0 | 0.0 | 0.065431 |  |
| 37 | kb_retrieval | 10 | 0.947368 | 0.682719 | 0.507407 | 0.5 | 0.13819 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 1 | 0.894737 | 0.874924 | 1.0 | 1.0 | 0.152332 |  |
| 40 | kb_retrieval | 1 | 1.0 | 0.963093 | 1.0 | 1.0 | 0.155325 |  |
| 41 | kb_retrieval | 20 | 0.642857 | 0.0 | 0.1 | 0.0 | 0.122877 |  |
| 42 | kb_retrieval | 20 | 0.166667 | 0.18191 | 0.272222 | 1.0 | 0.059746 |  |
| 43 | kb_retrieval | 2 | 0.75 | 0.0 | 1.0 | 1.0 | 0.141414 |  |
| 44 | kb_retrieval | 1 | 0.941176 | 0.795971 | 1.0 | 1.0 | 0.185604 |  |
| 45 | kb_retrieval | 1 | 0.5 | 0.731338 | 1.0 | 0.0 | 0.13969 |  |
| 46 | kb_retrieval | 1 | 0.888889 | 0.780607 | 1.0 | 0.0 | 0.159297 |  |
| 47 | kb_retrieval | 1 | 0.857143 | 0.0 | 1.0 | 1.0 | 0.140416 |  |
| 48 | kb_retrieval | 20 | 0.0 | 0.168658 | 0.1 | 1.0 | 0.088635 |  |
| 49 | kb_retrieval | 1 | 0.947368 | 0.894016 | 1.0 | 1.0 | 0.124033 |  |
| 50 | kb_retrieval | 1 | 1.0 | 0.859704 | 1.0 | 1.0 | 0.160181 |  |
| 63 | kb_retrieval | 1 | 1.0 | 0.879877 | 1.0 | 1.0 | 0.250426 |  |
| 64 | kb_retrieval | 1 | 0.888889 | 0.688852 | 1.0 | 0.5 | 0.288198 |  |
| 65 | kb_retrieval | 1 | 0.88 | 0.857543 | 1.0 | 1.0 | 0.350785 |  |
| 66 | kb_retrieval | 1 | 0.888889 | 0.847752 | 1.0 | 0.5 | 0.22708 |  |
| 67 | kb_retrieval | 7 | 0.464286 | 0.773548 | 1.0 | 1.0 | 0.184293 |  |
| 68 | kb_retrieval | 1 | 0.647059 | 0.903582 | 1.0 | 1.0 | 0.161198 |  |
| 69 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 70 | kb_retrieval | 1 | 0.615385 | 0.885078 | 1.0 | 1.0 | 0.183497 |  |
| 73 | kb_retrieval | 4 | 1.0 | 0.85243 | 0.583333 | 1.0 | 0.16959 |  |
| 74 | kb_retrieval | 1 | 0.8 | 0.581051 | 1.0 | 1.0 | 0.112426 |  |

## ⚠️ Empty retrieval contexts (retrieval bug, not eval)

Case IDs with no usable `retrieved_context`: 69


## Judge scores by category

- **kb_retrieval** (30): groundedness=4.57, plan_sanity=4.63, tone=4.8, safety=5.0

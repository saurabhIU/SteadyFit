# Eval summary (`hybrid_retrieval_v2`)

Total cases: 30

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.4 |
| plan_sanity | 4.6 |
| tone | 4.77 |
| safety | 4.97 |

## CRITICAL must-pass failures

None.

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.6525 |
| answer_relevancy | 0.638 |
| context_precision | 0.7793 |
| context_recall | 0.7286 |
| answer_correctness | 0.1857 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 30 | 0.6525 | 0.638 | 0.7793 | 0.7286 | 0.1857 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 15 | kb_retrieval | 1 | 0.9 | 0.708785 | 1.0 | 1.0 | 0.147258 |  |
| 27 | kb_retrieval | 2 | 0.944444 | 0.962983 | 0.0 | 0.0 | 0.049953 |  |
| 33 | kb_retrieval | 1 | 0.916667 | 0.853258 | 1.0 | 1.0 | 0.176388 |  |
| 34 | kb_retrieval | 20 | 0.166667 | 0.144703 | 0.563384 | 0.5 | 0.062995 |  |
| 35 | kb_retrieval | 7 | 0.791667 | 0.788625 | 1.0 | 1.0 | 0.218911 |  |
| 36 | kb_retrieval | 20 | 0.25 | 0.677971 | 0.0 | 0.0 | 0.072118 |  |
| 37 | kb_retrieval | 9 | 0.0 | 0.0 | 0.611111 | 0.5 | 0.568782 |  |
| 38 | kb_retrieval | 0 | — | — | — | — | — | oos_negative_case |
| 39 | kb_retrieval | 1 | 0.894737 | 0.793633 | 1.0 | 1.0 | 0.134961 |  |
| 40 | kb_retrieval | 1 | 0.888889 | 0.968889 | 1.0 | 1.0 | 0.155942 |  |
| 41 | kb_retrieval | 20 | 0.0 | 0.16529 | 0.05 | 0.5 | 0.068194 |  |
| 42 | kb_retrieval | 20 | 0.0 | 0.181913 | 0.2875 | 1.0 | 0.059746 |  |
| 43 | kb_retrieval | 2 | 0.931034 | 0.0 | 1.0 | 1.0 | 0.230244 |  |
| 44 | kb_retrieval | 1 | 0.894737 | 0.795971 | 1.0 | 1.0 | 0.19137 |  |
| 45 | kb_retrieval | 1 | 0.541667 | 0.906809 | 1.0 | 0.0 | 0.139851 |  |
| 46 | kb_retrieval | 1 | 0.703704 | 0.762328 | 1.0 | 0.0 | 0.480062 |  |
| 47 | kb_retrieval | 1 | 0.521739 | 0.716938 | 1.0 | 1.0 | 0.141533 |  |
| 48 | kb_retrieval | 20 | 0.0 | 0.168658 | 0.1 | 0.5 | 0.088635 |  |
| 49 | kb_retrieval | 1 | 1.0 | 0.970717 | 1.0 | 1.0 | 0.130185 |  |
| 50 | kb_retrieval | 1 | 1.0 | 0.859774 | 1.0 | 1.0 | 0.157786 |  |
| 63 | kb_retrieval | 1 | 1.0 | 0.785342 | 1.0 | 1.0 | 0.264434 |  |
| 64 | kb_retrieval | 1 | 0.65 | 0.932099 | 1.0 | 0.5 | 0.272502 |  |
| 65 | kb_retrieval | 1 | 0.909091 | 0.0 | 1.0 | 1.0 | 0.261596 |  |
| 66 | kb_retrieval | 1 | 0.894737 | 0.931872 | 1.0 | 0.4 | 0.292252 |  |
| 67 | kb_retrieval | 14 | 0.69697 | 0.785977 | 0.625 | 0.5 | 0.188511 |  |
| 68 | kb_retrieval | 1 | 0.615385 | 0.806 | 1.0 | 1.0 | 0.181209 |  |
| 69 | kb_retrieval | 0 | — | — | — | — | — | no retrieved context |
| 70 | kb_retrieval | 1 | 0.705882 | 0.819195 | 1.0 | 1.0 | 0.173296 |  |
| 73 | kb_retrieval | 5 | 0.857143 | 0.838027 | 0.583333 | 1.0 | 0.162244 |  |
| 74 | kb_retrieval | 1 | 0.59375 | 0.538261 | 1.0 | 1.0 | 0.127312 |  |

## ⚠️ Empty retrieval contexts (retrieval bug, not eval)

Case IDs with no usable `retrieved_context`: 69


## Judge scores by category

- **kb_retrieval** (30): groundedness=4.4, plan_sanity=4.6, tone=4.77, safety=4.97

# Eval summary (`try_profile_ux_full`)

Total cases: 96

## LLM-as-judge (coaching behavior, 0–5)

Covers tone, safety, plan sanity, and groundedness of the final reply.

| Metric | Avg |
|---|---|
| groundedness | 4.87 |
| plan_sanity | 4.89 |
| tone | 4.91 |
| safety | 4.96 |

## CRITICAL must-pass failures

None.

## RAGAS (retrieval / answer quality, 0–1)

Covers faithfulness & answer relevancy whenever contexts exist; context precision/recall & answer correctness when a ground-truth reference can be built from `expected_behavior` + `gold_sources`.

### Overall RAGAS averages

| Metric | Avg |
|---|---|
| faithfulness | 0.7415 |
| answer_relevancy | 0.7813 |
| context_precision | 0.4815 |
| context_recall | 0.1111 |
| answer_correctness | 0.3669 |

### RAGAS by category

| Category | N | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness |
|---|---|---|---|---|---|---|
| kb_retrieval | 30 | 0.8397 | 0.8813 | 0.1667 | 0.0 | 0.2645 |
| rag_personal | 14 | 0.7412 | 0.8299 | 1.0 | 0.3333 | 0.6257 |
| rag_web | 3 | 0.6438 | 0.6326 | 0.2778 | 0.0 | 0.2103 |

### RAGAS per case

| ID | Category | N ctx | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness | Notes |
|---|---|---|---|---|---|---|---|---|
| 7 | rag_personal | 1 | 0.733333 | 0.927043 | 1.0 | 0.5 | 0.667693 |  |
| 8 | rag_personal | 1 | 0.823529 | 0.744466 | 1.0 | 0.5 | 0.849116 |  |
| 9 | rag_personal | 1 | 0.666667 | 0.818331 | 1.0 | 0.0 | 0.360408 |  |
| 10 | rag_web | 2 | 0.764706 | 1.0 | 0.5 | 0.0 | 0.06078 |  |
| 11 | rag_web | 2 | 0.5 | 0.0 | 0.0 | 0.0 | 0.490476 |  |
| 12 | rag_web | 3 | 0.666667 | 0.897661 | 0.333333 | 0.0 | 0.079781 |  |
| 15 | kb_retrieval | 2 | 0.857143 | 0.718659 | 0.5 | 0.0 | 0.617242 |  |
| 27 | kb_retrieval | 3 | 0.928571 | 1.0 | 0.0 | 0.0 | 0.044871 |  |
| 33 | kb_retrieval | 2 | 0.733333 | 0.925206 | 0.0 | 0.0 | 0.131403 |  |

## Judge scores by category

- **adherence** (2): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **adversarial** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **autonomous** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **council_critique** (4): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **first_message** (6): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **gate_context** (5): groundedness=None, plan_sanity=None, tone=None, safety=None
- **kb_retrieval** (30): groundedness=4.67, plan_sanity=5.0, tone=5.0, safety=5.0
- **knowledge** (1): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **memory** (3): groundedness=None, plan_sanity=None, tone=None, safety=None
- **nutrition** (4): groundedness=4.0, plan_sanity=4.25, tone=4.0, safety=4.5
- **onboarding** (4): groundedness=4.75, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_personal** (14): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **rag_web** (3): groundedness=5.0, plan_sanity=4.33, tone=5.0, safety=5.0
- **safety** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **schedule** (3): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0
- **topic_interrupt** (3): groundedness=None, plan_sanity=None, tone=None, safety=None
- **try_profile_ux** (4): groundedness=5.0, plan_sanity=5.0, tone=5.0, safety=5.0

"""Sync golden set → LangSmith Dataset and run a tracked Experiment.

Experiments show per-example scores + summary averages in the LangSmith UI
(Datasets → your dataset → Experiments), which is richer than trace-only runs.

  LANGCHAIN_API_KEY=... \\
  LANGCHAIN_TRACING_V2=true \\
  uv run python evals/run_evals.py --experiment
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Any, Callable

from langsmith import Client

from ragas_metrics import RAGAS_METRIC_KEYS

JUDGE_DIMS = ("groundedness", "plan_sanity", "tone", "safety")
DEFAULT_DATASET = "steadyfit-golden"


def _dataset_name() -> str:
    return os.environ.get("LANGSMITH_DATASET", DEFAULT_DATASET)


def sync_dataset(client: Client, rows: list[dict]) -> str:
    """Replace dataset examples with the current golden JSONL rows."""
    name = _dataset_name()
    if client.has_dataset(dataset_name=name):
        dataset = client.read_dataset(dataset_name=name)
        for ex in client.list_examples(dataset_id=dataset.id):
            client.delete_example(ex.id)
    else:
        dataset = client.create_dataset(
            dataset_name=name,
            description=(
                "SteadyFit golden eval set (schedule, nutrition, KB RAG, adversarial, "
                "onboarding). Synced from evals/golden_dataset.jsonl."
            ),
        )

    examples = []
    for row in rows:
        examples.append({
            "inputs": {
                "id": row["id"],
                "category": row["category"],
                "question": row["input"],
                "row": row,
            },
            "outputs": {
                "expected_behavior": row["expected_behavior"],
            },
            "metadata": {
                "category": row["category"],
                "case_id": row["id"],
                "gold_sources": row.get("gold_sources") or row.get("gold_context_source"),
            },
        })
    client.create_examples(dataset_id=dataset.id, examples=examples)
    return name


def _dim_evaluator(dim: str) -> Callable:
    def evaluator(run, example) -> dict:  # noqa: ARG001
        scores = (run.outputs or {}).get("judge_scores") or {}
        val = scores.get(dim)
        if not isinstance(val, (int, float)):
            return {"key": dim, "score": None}
        return {
            "key": dim,
            # LangSmith experiment table expects 0–1 friendly scores
            "score": float(val) / 5.0,
            "comment": str(scores.get("notes") or "")[:300],
        }

    return evaluator


def _ragas_evaluator(dim: str) -> Callable:
    def evaluator(run, example) -> dict:  # noqa: ARG001
        scores = (run.outputs or {}).get("ragas") or {}
        val = scores.get(dim)
        if not isinstance(val, (int, float)):
            return {"key": dim, "score": None}
        return {"key": dim, "score": float(val)}

    return evaluator


def _avg_summary(dim: str, *, source: str = "judge_scores", scale: float = 5.0) -> Callable:
    def summary_evaluator(runs, examples) -> dict:  # noqa: ARG001
        vals = []
        for run in runs:
            scores = (run.outputs or {}).get(source) or {}
            val = scores.get(dim)
            if isinstance(val, (int, float)):
                vals.append(float(val))
        if not vals:
            return {"key": f"avg_{dim}", "score": None}
        avg = sum(vals) / len(vals)
        return {
            "key": f"avg_{dim}",
            "score": (avg / scale) if scale != 1.0 else avg,
            "comment": f"mean {avg:.4f} over {len(vals)} cases (source={source})",
        }

    return summary_evaluator


def _examples_from_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            "inputs": {
                "id": row["id"],
                "category": row["category"],
                "question": row["input"],
                "row": row,
            },
            "outputs": {"expected_behavior": row["expected_behavior"]},
            "metadata": {
                "category": row["category"],
                "case_id": row["id"],
                "gold_sources": row.get("gold_sources") or row.get("gold_context_source"),
            },
        }
        for row in rows
    ]


def run_experiment(
    *,
    rows: list[dict],
    invoke_case: Callable,
    judge_reply: Callable,
    ragas_scores: Callable,
    build_graph: Callable,
    collect_local: bool = True,
    sync_full_dataset: bool = True,
) -> tuple[list[dict], Any]:
    """Run LangSmith evaluate(); optionally also return local-style result dicts.

    When ``sync_full_dataset`` is False (smoke / ``--ids``), examples are passed
    inline so we do not wipe the shared LangSmith dataset.
    """
    if not os.environ.get("LANGCHAIN_API_KEY") and not os.environ.get("LANGSMITH_API_KEY"):
        raise SystemExit(
            "LANGCHAIN_API_KEY (or LANGSMITH_API_KEY) required for --experiment"
        )

    client = Client()
    if sync_full_dataset:
        dataset_name = sync_dataset(client, rows)
        data: Any = dataset_name
        print(f"Synced {len(rows)} examples → LangSmith dataset '{dataset_name}'")
    else:
        data = _examples_from_rows(rows)
        print(f"Running experiment on {len(rows)} inline examples (dataset not overwritten)")

    graph = build_graph()
    from app.config import get_llm, settings

    judge = get_llm(settings.judge_model)
    local_results: list[dict] = []
    local_lock = threading.Lock()

    def target(inputs: dict) -> dict:
        row = inputs.get("row") or {
            "id": inputs.get("id"),
            "category": inputs.get("category"),
            "input": inputs.get("question") or inputs.get("input"),
            "expected_behavior": "",
        }
        print(f"  [{row.get('id')}] {row.get('category')} …", flush=True)
        out = invoke_case(graph, row)
        scores = judge_reply(judge, row, out["reply"])
        ragas = ragas_scores(row, out["reply"], out.get("contexts") or [])
        payload = {
            "reply": out.get("reply"),
            "contexts": out.get("contexts") or [],
            "pending_approval": out.get("pending_approval"),
            "judge_scores": scores,
            "ragas": ragas,
            "category": row.get("category"),
            "case_id": row.get("id"),
        }
        if collect_local:
            with local_lock:
                local_results.append({
                    "id": row.get("id"),
                    "category": row.get("category"),
                    "input": row.get("input"),
                    "expected_behavior": row.get("expected_behavior"),
                    **payload,
                })
        return payload

    prefix = os.environ.get(
        "LANGSMITH_EXPERIMENT_PREFIX",
        f"steadyfit-eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
    )
    # Keep concurrency low: shared Postgres checkpointer + embedding calls.
    concurrency = int(os.environ.get("LANGSMITH_MAX_CONCURRENCY", "1"))

    evaluators = [_dim_evaluator(d) for d in JUDGE_DIMS] + [
        _ragas_evaluator(d) for d in RAGAS_METRIC_KEYS
    ]
    summary_evaluators = [
        _avg_summary(d, source="judge_scores", scale=5.0) for d in JUDGE_DIMS
    ] + [
        _avg_summary(d, source="ragas", scale=1.0) for d in RAGAS_METRIC_KEYS
    ]

    experiment = client.evaluate(
        target,
        data=data,
        evaluators=evaluators,
        summary_evaluators=summary_evaluators,
        experiment_prefix=prefix,
        description=(
            f"SteadyFit golden eval ({len(rows)} cases). "
            "Judge dims + RAGAS (groundedness, faithfulness, context recall/precision, noise)."
        ),
        metadata={
            "harness": "evals/run_evals.py",
            "n_cases": len(rows),
            "dataset_file": "evals/golden_dataset.jsonl",
            "synced_dataset": sync_full_dataset,
        },
        max_concurrency=concurrency,
        blocking=True,
    )

    # Sort local results by id for stable summary.md
    local_results.sort(key=lambda r: (r.get("id") is None, r.get("id")))
    return local_results, experiment

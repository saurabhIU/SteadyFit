"""Eval harness: LLM-as-judge + optional RAGAS on RAG categories.

Run (local JSON/MD only):
  uv run python evals/run_evals.py

Run as LangSmith Experiment (dataset + summary table in UI):
  LANGCHAIN_TRACING_V2=true uv run python evals/run_evals.py --experiment

Requires: AI_GATEWAY_API_KEY, DATABASE_URL
Optional: TAVILY_API_KEY (rag_web cases)
RAGAS (rag_* / kb_retrieval): answer_groundedness, faithfulness,
  context_recall, context_precision, noise_sensitivity
  (uses AI gateway judge model; needs contexts + expected_behavior reference)
LangSmith experiment: LANGCHAIN_API_KEY + --experiment
  LANGSMITH_DATASET=steadyfit-golden (default)
  LANGSMITH_EXPERIMENT_PREFIX=steadyfit-eval-…
  LANGSMITH_MAX_CONCURRENCY=1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Load .env into os.environ before LangSmith/LangChain import (pydantic Settings
# ignores LANGCHAIN_* extras, so tracing keys would otherwise be missing).
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import get_llm, settings
from helpers import (
    format_summary_table,
    invoke_case,
    judge_reply,
    load_golden_rows,
    ragas_scores,
    summarize_results,
)


def _write_artifacts(results: list[dict]) -> dict:
    summary = summarize_results(results)
    out_dir = Path("evals")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (out_dir / "summary.md").write_text(format_summary_table(summary))
    print(format_summary_table(summary))
    print("Wrote evals/results.json, evals/summary.json, evals/summary.md")
    return summary


def run_local(rows: list[dict]) -> list[dict]:
    from app.graph.build import build_graph

    graph = build_graph()
    judge = get_llm(settings.judge_model)
    results = []
    print(f"Running {len(rows)} eval cases (local)…")
    for row in rows:
        print(f"  [{row['id']}] {row['category']} …", flush=True)
        out = invoke_case(graph, row)
        scores = judge_reply(judge, row, out["reply"])
        ragas = ragas_scores(row, out["reply"], out.get("contexts") or [])
        results.append({
            "id": row["id"],
            "category": row["category"],
            "input": row["input"],
            "expected_behavior": row["expected_behavior"],
            "reply": out["reply"],
            "pending_approval": out.get("pending_approval"),
            "contexts": out.get("contexts") or [],
            "judge_scores": scores,
            "ragas": ragas,
        })
    return results


def run():
    parser = argparse.ArgumentParser(description="SteadyFit golden eval harness")
    parser.add_argument(
        "--experiment",
        action="store_true",
        help="Sync dataset + run LangSmith Experiment (summary in Experiments UI)",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default="",
        help="Comma-separated case ids to run (smoke), e.g. 33,39,50",
    )
    args = parser.parse_args()

    if not settings.ai_gateway_api_key:
        raise SystemExit("AI_GATEWAY_API_KEY is required to run evals")
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is required to run evals")

    rows = load_golden_rows(Path("evals/golden_dataset.jsonl"))
    if args.ids.strip():
        want = {int(x.strip()) for x in args.ids.split(",") if x.strip()}
        rows = [r for r in rows if r["id"] in want]
        if not rows:
            raise SystemExit(f"No cases matched --ids {args.ids}")

    if args.experiment:
        from app.graph.build import build_graph
        from langsmith_experiment import run_experiment

        # Full-file runs sync the shared LangSmith dataset; --ids smokes do not.
        full_file = not bool(args.ids.strip())
        results, experiment = run_experiment(
            rows=rows,
            invoke_case=invoke_case,
            judge_reply=judge_reply,
            ragas_scores=ragas_scores,
            build_graph=build_graph,
            sync_full_dataset=full_file,
        )
        _write_artifacts(results)
        url = getattr(experiment, "experiment_url", None) or getattr(
            experiment, "url", None
        )
        print("LangSmith experiment finished.")
        if url:
            print(f"Open: {url}")
        else:
            print(
                "Open LangSmith → Datasets → "
                f"{__import__('os').environ.get('LANGSMITH_DATASET', 'steadyfit-golden')} "
                "→ Experiments"
            )
        return

    results = run_local(rows)
    _write_artifacts(results)


if __name__ == "__main__":
    run()

"""Eval harness: LLM-as-judge + optional RAGAS on RAG categories.

Run:  uv run python evals/run_evals.py
Requires: AI_GATEWAY_API_KEY, DATABASE_URL
Optional: OPENAI_API_KEY (RAGAS), TAVILY_API_KEY (rag_web cases)
"""
import json
import sys
from pathlib import Path

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


def run():
    if not settings.ai_gateway_api_key:
        raise SystemExit("AI_GATEWAY_API_KEY is required to run evals")
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is required to run evals")

    from app.graph.build import build_graph

    graph = build_graph()
    judge = get_llm(settings.judge_model)
    rows = load_golden_rows(Path("evals/golden_dataset.jsonl"))
    results = []

    print(f"Running {len(rows)} eval cases…")
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

    summary = summarize_results(results)
    out_dir = Path("evals")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (out_dir / "summary.md").write_text(format_summary_table(summary))

    print(format_summary_table(summary))
    print(f"Wrote evals/results.json, evals/summary.json, evals/summary.md")


if __name__ == "__main__":
    run()

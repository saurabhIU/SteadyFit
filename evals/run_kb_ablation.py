"""Re-run the kb_retrieval golden-dataset slice through dense-only and hybrid
retrieval now that the app.rag.retriever param-ordering bug is fixed.

Produces `baseline_fixed_v2` (plain retrieve(), dense cosine only) and
`hybrid_retrieval_v2` (retrieve_hybrid(), dense+FTS RRF) — deliberately
distinct labels from the old, contaminated `baseline_fixed` /
`hybrid_retrieval` artifacts so the two are never confused.

Usage:
  uv run python evals/run_kb_ablation.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import load_golden_rows  # noqa: E402
from run_evals import _write_artifacts, run_local  # noqa: E402


def _dense_only_retrieve_kb(query: str, *, doc_types=None, modality=None, k: int = 5):
    """Mirrors app.rag.retriever.retrieve_kb but forces the dense-only path."""
    from app.rag.retriever import retrieve

    types = doc_types or ["kb_exercise", "kb_guide", "kb_template", "kb_science"]
    return retrieve(query, doc_types=types, modality=modality, k=k)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ids",
        type=str,
        default="",
        help="Comma-separated case ids for a smoke run (e.g. 15,27,63)",
    )
    parser.add_argument(
        "--dense-label",
        type=str,
        default="baseline_fixed_v2",
    )
    parser.add_argument(
        "--hybrid-label",
        type=str,
        default="hybrid_retrieval_v2",
    )
    args = parser.parse_args()

    from app.config import settings

    if not settings.ai_gateway_api_key:
        raise SystemExit("AI_GATEWAY_API_KEY is required to run evals")
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is required to run evals")

    rows = load_golden_rows(Path("evals/golden_dataset.jsonl"))
    kb_rows = [r for r in rows if r.get("category") == "kb_retrieval"]
    if args.ids.strip():
        want = {int(x.strip()) for x in args.ids.split(",") if x.strip()}
        kb_rows = [r for r in kb_rows if r["id"] in want]
    print(f"kb_retrieval slice: {len(kb_rows)} cases -> ids {[r['id'] for r in kb_rows]}")

    import app.tools.agent_tools as agent_tools

    real_retrieve_kb = agent_tools.retrieve_kb
    dense_label, hybrid_label = args.dense_label, args.hybrid_label

    # ---- Pass 1: dense-only (plain retrieve()) -> baseline_fixed_v2 ----
    agent_tools.retrieve_kb = _dense_only_retrieve_kb
    try:
        dense_results = run_local(kb_rows, label=dense_label)
    finally:
        agent_tools.retrieve_kb = real_retrieve_kb
    _write_artifacts(dense_results, label=dense_label)

    # ---- Pass 2: hybrid dense+FTS RRF (retrieve_hybrid(), current default) ----
    # agent_tools.retrieve_kb is already restored to the real retrieve_kb,
    # which routes to retrieve_hybrid() per app/rag/retriever.py.
    hybrid_results = run_local(kb_rows, label=hybrid_label)
    _write_artifacts(hybrid_results, label=hybrid_label)

    # ---- Sanity check: zero [kb:error] fallback strings in either run ----
    def _kb_error_ids(results: list[dict]) -> list[int]:
        return [
            r["id"]
            for r in results
            if any("[kb:error]" in c for c in (r.get("contexts") or []))
        ]

    dense_errors = _kb_error_ids(dense_results)
    hybrid_errors = _kb_error_ids(hybrid_results)
    print("\n=== [kb:error] sanity check ===")
    print(f"{dense_label} (dense-only): {len(dense_errors)} cases with [kb:error] -> {dense_errors}")
    print(f"{hybrid_label} (hybrid):   {len(hybrid_errors)} cases with [kb:error] -> {hybrid_errors}")

    Path("evals/kb_ablation_sanity.json").write_text(
        json.dumps(
            {
                "dense_error_ids": dense_errors,
                "hybrid_error_ids": hybrid_errors,
                "dense_n": len(dense_results),
                "hybrid_n": len(hybrid_results),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

"""Eval harness: LLM-as-judge + RAGAS on RAG categories.

Run (local JSON/MD only, tracing forced off):
  uv run python evals/run_evals.py
  uv run python evals/run_evals.py --label baseline
  uv run python evals/run_evals.py --label hybrid_retrieval

Compare two labeled runs (Task 5/6 before/after):
  uv run python evals/run_evals.py --compare baseline hybrid_retrieval

LangSmith Experiment (optional; does not require tracing for local mode):
  uv run python evals/run_evals.py --experiment

Requires: AI_GATEWAY_API_KEY, DATABASE_URL, OPENAI_API_KEY (embeddings for RAGAS)
Optional: TAVILY_API_KEY (rag_web cases)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Local evals must not depend on LangSmith — force tracing off before imports.
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
# Re-assert after dotenv so a true env in .env cannot re-enable tracing for the harness.
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import get_llm, settings
from helpers import (
    compare_labeled_summaries,
    critique_structural_failure,
    format_summary_table,
    invoke_case,
    judge_reply,
    load_golden_rows,
    ragas_scores,
    summarize_results,
)


def _out_paths(label: str | None) -> tuple[Path, Path, Path]:
    out_dir = Path("evals")
    out_dir.mkdir(exist_ok=True)
    if label:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in label.strip())
        return (
            out_dir / f"results_{safe}.json",
            out_dir / f"summary_{safe}.json",
            out_dir / f"summary_{safe}.md",
        )
    return (
        out_dir / "results.json",
        out_dir / "summary.json",
        out_dir / "summary.md",
    )


def _write_artifacts(results: list[dict], *, label: str | None = None) -> dict:
    summary = summarize_results(results)
    if label:
        summary["label"] = label
    results_path, summary_json_path, summary_md_path = _out_paths(label)
    results_path.write_text(json.dumps(results, indent=2))
    summary_json_path.write_text(json.dumps(summary, indent=2))
    md = format_summary_table(summary, label=label)
    summary_md_path.write_text(md)
    # Always refresh canonical paths when unlabeled; when labeled, also update summary.md
    # so `evals/summary.md` shows the latest run.
    if label:
        (Path("evals") / "summary.md").write_text(md)
        (Path("evals") / "results.json").write_text(json.dumps(results, indent=2))
        (Path("evals") / "summary.json").write_text(json.dumps(summary, indent=2))
    print(md)
    print(
        f"Wrote {results_path}, {summary_json_path}, {summary_md_path}"
        + (f" (label={label})" if label else "")
    )
    empty = summary.get("empty_context_ids") or []
    if empty:
        print(
            "⚠️ Empty retrieval contexts (retrieval bug): "
            + ", ".join(str(i) for i in empty)
        )
    return summary


def _partial_path(label: str | None) -> Path:
    results_path, _, _ = _out_paths(label)
    return results_path.with_suffix(".partial.json")


def _load_partial(label: str | None) -> list[dict]:
    path = _partial_path(label)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_partial(results: list[dict], label: str | None) -> None:
    path = _partial_path(label)
    path.write_text(json.dumps(results, indent=2))


def run_local(
    rows: list[dict],
    *,
    label: str | None = None,
    resume: bool = False,
) -> list[dict]:
    from app.graph.build import build_graph

    assert os.environ.get("LANGCHAIN_TRACING_V2", "").lower() in {
        "",
        "false",
        "0",
        "no",
        "off",
    }, "Eval harness must run with LangSmith tracing disabled"

    graph = build_graph()
    judge = get_llm(settings.judge_model)
    results: list[dict] = []
    done_ids: set[int] = set()
    if resume:
        results = _load_partial(label)
        done_ids = {int(r["id"]) for r in results if "id" in r}
        if done_ids:
            print(f"Resuming: {len(done_ids)} cases already in {_partial_path(label)}")

    todo = [r for r in rows if int(r["id"]) not in done_ids]
    print(
        f"Running {len(todo)} eval cases "
        f"({len(done_ids)} skipped; local, tracing off)…"
    )
    for row in todo:
        print(f"  [{row['id']}] {row['category']} …", flush=True)
        try:
            out = invoke_case(graph, row)
            scores = judge_reply(judge, row, out["reply"])
            struct_err = critique_structural_failure(row, out)
            try:
                ragas = ragas_scores(row, out["reply"], out.get("contexts") or [])
            except Exception as exc:
                ragas = {"error": f"ragas crashed: {exc}"[:240]}
            results.append({
                "id": row["id"],
                "category": row["category"],
                "input": row["input"],
                "expected_behavior": row["expected_behavior"],
                "reply": out["reply"],
                "scope": out.get("scope"),
                "must_pass": bool(row.get("must_pass")),
                "expect_scope": row.get("expect_scope"),
                "priority": row.get("priority"),
                "pending_approval": out.get("pending_approval"),
                "contexts": out.get("contexts") or [],
                "n_contexts": len(out.get("contexts") or []),
                "judge_scores": scores,
                "ragas": ragas,
                "critique_verdict": out.get("critique_verdict"),
                "critique_rounds": out.get("critique_rounds"),
                "coaching_team": out.get("coaching_team"),
                "coaching_team_transcript": out.get("coaching_team_transcript"),
                "critique_structural_error": struct_err,
                "vision_usage": out.get("vision_usage"),
            })
            if struct_err:
                print(f"    ! structural: {struct_err}", flush=True)
            if out.get("vision_usage"):
                print(f"    vision_usage: {out.get('vision_usage')}", flush=True)
        except Exception as exc:
            print(f"    ! case {row['id']} failed: {exc}", flush=True)
            results.append({
                "id": row["id"],
                "category": row["category"],
                "input": row["input"],
                "expected_behavior": row["expected_behavior"],
                "reply": "",
                "scope": None,
                "must_pass": bool(row.get("must_pass")),
                "expect_scope": row.get("expect_scope"),
                "priority": row.get("priority"),
                "pending_approval": None,
                "contexts": [],
                "n_contexts": 0,
                "judge_scores": {},
                "ragas": None,
                "error": str(exc)[:300],
            })
        _save_partial(results, label)
    return results


def _compare(label_a: str, label_b: str) -> None:
    path_a = Path("evals") / f"summary_{label_a}.json"
    path_b = Path("evals") / f"summary_{label_b}.json"
    if not path_a.exists() or not path_b.exists():
        raise SystemExit(
            f"Need {path_a} and {path_b}. Run with --label {label_a} and "
            f"--label {label_b} first."
        )
    a = json.loads(path_a.read_text())
    b = json.loads(path_b.read_text())
    md = compare_labeled_summaries(a, b, label_a=label_a, label_b=label_b)
    out = Path("evals") / f"compare_{label_a}_vs_{label_b}.md"
    out.write_text(md)
    print(md)
    print(f"Wrote {out}")


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
    parser.add_argument(
        "--category",
        type=str,
        default="",
        help="Only run cases in this category (e.g. council_critique)",
    )
    parser.add_argument(
        "--label",
        type=str,
        default="",
        help="Save artifacts as results_<label>.json / summary_<label>.* "
        "(e.g. baseline, hybrid_retrieval)",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("LABEL_A", "LABEL_B"),
        help="Render a before/after table from two labeled summary_*.json files",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip case ids already present in results_<label>.partial.json",
    )
    args = parser.parse_args()

    if args.compare:
        _compare(args.compare[0], args.compare[1])
        return

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
    if args.category.strip():
        cat = args.category.strip()
        rows = [r for r in rows if r.get("category") == cat]
        if not rows:
            raise SystemExit(f"No cases matched --category {cat}")

    label = args.label.strip() or None

    if args.experiment:
        from app.graph.build import build_graph
        from langsmith_experiment import run_experiment

        full_file = not bool(args.ids.strip())
        results, experiment = run_experiment(
            rows=rows,
            invoke_case=invoke_case,
            judge_reply=judge_reply,
            ragas_scores=ragas_scores,
            build_graph=build_graph,
            sync_full_dataset=full_file,
        )
        _write_artifacts(results, label=label)
        url = getattr(experiment, "experiment_url", None) or getattr(
            experiment, "url", None
        )
        print("LangSmith experiment finished.")
        if url:
            print(f"Open: {url}")
        else:
            print(
                "Open LangSmith → Datasets → "
                f"{os.environ.get('LANGSMITH_DATASET', 'steadyfit-golden')} "
                "→ Experiments"
            )
        return

    results = run_local(rows, label=label, resume=args.resume)
    _write_artifacts(results, label=label)
    partial = _partial_path(label)
    if partial.exists():
        partial.unlink(missing_ok=True)


if __name__ == "__main__":
    run()

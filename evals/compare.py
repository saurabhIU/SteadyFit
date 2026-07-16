#!/usr/bin/env python3
"""Compare two labeled eval result files (Task 6 kb_retrieval focus).

Usage:
  uv run python evals/compare.py --a baseline_fixed --b hybrid_retrieval

Reads evals/results_<label>.json, aggregates RAGAS for kb_retrieval only,
prints a markdown table, and writes evals/comparison_<a>_vs_<b>.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

METRIC_KEYS = (
    "context_precision",
    "context_recall",
    "faithfulness",
    "answer_relevancy",
    "answer_correctness",
)


def _avg_kb(results: list[dict]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    kb = [r for r in results if r.get("category") == "kb_retrieval"]
    for key in METRIC_KEYS:
        vals = [
            r["ragas"][key]
            for r in kb
            if isinstance(r.get("ragas"), dict)
            and isinstance(r["ragas"].get(key), (int, float))
        ]
        out[key] = round(sum(vals) / len(vals), 4) if vals else None
    out["_n"] = len(kb)  # type: ignore[assignment]
    out["_n_scored"] = sum(  # type: ignore[assignment]
        1
        for r in kb
        if isinstance(r.get("ragas"), dict)
        and any(isinstance(r["ragas"].get(k), (int, float)) for k in METRIC_KEYS)
    )
    return out


def _fmt(v: float | None) -> str:
    return f"{v:.4f}" if isinstance(v, (int, float)) else "—"


def _delta(a: float | None, b: float | None) -> str:
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return "—"
    d = b - a
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.4f}"


def compare(label_a: str, label_b: str) -> str:
    path_a = Path("evals") / f"results_{label_a}.json"
    path_b = Path("evals") / f"results_{label_b}.json"
    if not path_a.exists() or not path_b.exists():
        raise SystemExit(f"Need {path_a} and {path_b}")
    a = _avg_kb(json.loads(path_a.read_text()))
    b = _avg_kb(json.loads(path_b.read_text()))
    lines = [
        f"# Comparison (`kb_retrieval`): `{label_a}` vs `{label_b}`",
        "",
        f"Cases: {label_a} n={a.get('_n')} (scored {a.get('_n_scored')}); "
        f"{label_b} n={b.get('_n')} (scored {b.get('_n_scored')})",
        "",
        f"| Metric | {label_a} | {label_b} | delta |",
        "|---|---|---|---|",
    ]
    for key in METRIC_KEYS:
        va, vb = a.get(key), b.get(key)
        lines.append(f"| {key} | {_fmt(va)} | {_fmt(vb)} | {_delta(va, vb)} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare kb_retrieval RAGAS across labels")
    parser.add_argument("--a", required=True, help="Baseline label (e.g. baseline_fixed)")
    parser.add_argument("--b", required=True, help="Improved label (e.g. hybrid_retrieval)")
    args = parser.parse_args()
    md = compare(args.a, args.b)
    out = Path("evals") / f"comparison_{args.a}_vs_{args.b}.md"
    out.write_text(md)
    print(md)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

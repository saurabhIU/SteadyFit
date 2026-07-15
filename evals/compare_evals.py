#!/usr/bin/env python3
"""Compare two labeled eval summary files (Task 5/6 before/after).

Usage:
  uv run python evals/compare_evals.py baseline hybrid_retrieval
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import compare_labeled_summaries  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: uv run python evals/compare_evals.py <label_a> <label_b>"
        )
    label_a, label_b = sys.argv[1], sys.argv[2]
    path_a = Path("evals") / f"summary_{label_a}.json"
    path_b = Path("evals") / f"summary_{label_b}.json"
    if not path_a.exists() or not path_b.exists():
        raise SystemExit(f"Missing {path_a} or {path_b}")
    md = compare_labeled_summaries(
        json.loads(path_a.read_text()),
        json.loads(path_b.read_text()),
        label_a=label_a,
        label_b=label_b,
    )
    out = Path("evals") / f"compare_{label_a}_vs_{label_b}.md"
    out.write_text(md)
    print(md)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

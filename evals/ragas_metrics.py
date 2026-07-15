"""RAGAS metric suite for SteadyFit RAG eval cases.

Records (0–1 unless noted):
  - answer_groundedness  (RAGAS ResponseGroundedness)
  - faithfulness
  - context_recall
  - context_precision
  - noise_sensitivity

Context recall / precision / noise need a ``reference``; we build one from
``expected_behavior`` + ``gold_sources`` on the golden row.
"""
from __future__ import annotations

from typing import Any

RAG_CATEGORIES = {"rag_personal", "rag_web", "kb_retrieval"}

RAGAS_METRIC_KEYS = (
    "answer_groundedness",
    "faithfulness",
    "context_recall",
    "context_precision",
    "noise_sensitivity",
)

# Normalize whatever name RAGAS emits → our stable keys
_RAW_KEY_ALIASES = {
    "answer_groundedness": "answer_groundedness",
    "nv_response_groundedness": "answer_groundedness",
    "response_groundedness": "answer_groundedness",
    "faithfulness": "faithfulness",
    "context_recall": "context_recall",
    "context_precision": "context_precision",
    "llm_context_precision_without_reference": "context_precision",
    "llm_context_precision_with_reference": "context_precision",
    "noise_sensitivity": "noise_sensitivity",
    "noise_sensitivity(mode=relevant)": "noise_sensitivity",
    "noise_sensitivity(mode=irrelevant)": "noise_sensitivity",
}


def _alias_raw_key(key: str) -> str | None:
    k = str(key)
    if k in _RAW_KEY_ALIASES:
        return _RAW_KEY_ALIASES[k]
    # RAGAS sometimes emits names like "noise_sensitivity(mode=relevant)"
    if k.startswith("noise_sensitivity"):
        return "noise_sensitivity"
    if "groundedness" in k:
        return "answer_groundedness"
    return None


def build_reference(row: dict) -> str:
    """Proxy reference for retrieval metrics (recall / precision / noise)."""
    parts: list[str] = []
    expected = (row.get("expected_behavior") or "").strip()
    if expected:
        parts.append(expected)
    gold = row.get("gold_sources") or row.get("gold_context_source")
    if isinstance(gold, list) and gold:
        parts.append("Gold sources: " + ", ".join(str(g) for g in gold))
    elif isinstance(gold, str) and gold.strip():
        parts.append(f"Gold sources: {gold.strip()}")
    return "\n".join(parts).strip() or (row.get("input") or "")


def normalize_ragas_row(raw: dict) -> dict[str, Any]:
    """Map RAGAS column names → stable keys; keep only numeric metric scores."""
    out: dict[str, Any] = {}
    for key, val in raw.items():
        mapped = _alias_raw_key(str(key))
        if mapped is None:
            continue
        if isinstance(val, (int, float)) and val == val:  # reject NaN
            out[mapped] = round(float(val), 6)
    return out


def _empty_metric_bundle(**extra: Any) -> dict[str, Any]:
    bundle = {k: None for k in RAGAS_METRIC_KEYS}
    bundle.update(extra)
    return bundle


def ragas_scores(row: dict, reply: str, contexts: list[str]) -> dict | None:
    """Run the RAGAS suite for one case. Returns None for non-RAG categories."""
    if row.get("category") not in RAG_CATEGORIES:
        return None
    if row.get("category") == "kb_retrieval" and "crypto" in row.get("input", "").lower():
        return _empty_metric_bundle(skipped="oos_negative_case")
    if not contexts:
        return _empty_metric_bundle(skipped="no retrieved context")

    try:
        from datasets import Dataset
        from langchain_openai import ChatOpenAI
        from ragas import evaluate
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import (
            NoiseSensitivity,
            ResponseGroundedness,
            context_precision,
            context_recall,
            faithfulness,
        )
    except ImportError as exc:
        return _empty_metric_bundle(skipped=f"ragas import failed: {exc}"[:180])

    reference = build_reference(row)
    try:
        # InstructorLLM (ragas default) lacks agenerate_text needed by
        # ResponseGroundedness / NoiseSensitivity — use LangChain + gateway.
        from app.config import gateway_api_key, settings

        judge = ChatOpenAI(
            model=settings.judge_model,
            api_key=gateway_api_key(),
            base_url=settings.ai_gateway_base_url,
            temperature=0,
        )
        ragas_llm = LangchainLLMWrapper(judge)

        dataset = Dataset.from_dict({
            "user_input": [row["input"]],
            "response": [reply],
            "retrieved_contexts": [list(contexts)],
            "reference": [reference],
            # v1 aliases — convert_v1_to_v2 accepts either shape
            "question": [row["input"]],
            "answer": [reply],
            "contexts": [list(contexts)],
        })
        metrics = [
            ResponseGroundedness(),
            faithfulness,
            context_recall,
            context_precision,
            NoiseSensitivity(),
        ]
        result: Any = evaluate(dataset, metrics=metrics, llm=ragas_llm)
        raw: dict[str, Any] = {}
        to_pandas = getattr(result, "to_pandas", None)
        if callable(to_pandas):
            frame: Any = to_pandas()
            raw = frame.iloc[0].to_dict()
        else:
            scores = getattr(result, "scores", None)
            if isinstance(scores, list) and scores and isinstance(scores[0], dict):
                raw = dict(scores[0])
            elif isinstance(result, dict):
                raw = dict(result)
            else:
                return _empty_metric_bundle(error=repr(result)[:200])

        normalized = normalize_ragas_row(raw)
        bundle = _empty_metric_bundle()
        bundle.update(normalized)
        # Preserve any non-metric diagnostics lightly
        if not normalized:
            bundle["error"] = "ragas returned no numeric scores"
            bundle["raw_keys"] = sorted(str(k) for k in raw.keys())[:20]
        return bundle
    except Exception as exc:
        return _empty_metric_bundle(error=str(exc)[:240])


def average_ragas(results: list[dict]) -> dict[str, float | None]:
    """Mean of each RAGAS key across cases that have numeric scores."""
    avgs: dict[str, float | None] = {}
    for key in RAGAS_METRIC_KEYS:
        vals = [
            r["ragas"][key]
            for r in results
            if isinstance(r.get("ragas"), dict)
            and isinstance(r["ragas"].get(key), (int, float))
        ]
        avgs[key] = round(sum(vals) / len(vals), 4) if vals else None
    return avgs

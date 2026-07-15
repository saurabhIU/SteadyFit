"""RAGAS metric suite for SteadyFit RAG eval cases.

Metrics (0–1):
  - faithfulness, answer_relevancy — all rag-flavored categories with contexts
  - context_precision, context_recall, answer_correctness — only when a
    ground-truth / reference can be built from expected_behavior + gold_sources

Uses the Vercel AI Gateway judge LLM + project embeddings (OpenAI-compatible).
"""
from __future__ import annotations

import re
from typing import Any

RAG_CATEGORIES = {"rag_personal", "rag_web", "kb_retrieval", "memory"}

# Always attempted when contexts exist
RAGAS_ALWAYS_KEYS = (
    "faithfulness",
    "answer_relevancy",
)

# Requires a reference / ground_truth
RAGAS_GT_KEYS = (
    "context_precision",
    "context_recall",
    "answer_correctness",
)

RAGAS_METRIC_KEYS = RAGAS_ALWAYS_KEYS + RAGAS_GT_KEYS

_RAW_KEY_ALIASES = {
    "faithfulness": "faithfulness",
    "answer_relevancy": "answer_relevancy",
    "answer_relevance": "answer_relevancy",
    "response_relevancy": "answer_relevancy",
    "context_recall": "context_recall",
    "context_precision": "context_precision",
    "llm_context_precision_without_reference": "context_precision",
    "llm_context_precision_with_reference": "context_precision",
    "answer_correctness": "answer_correctness",
}

_UNTRUSTED_RE = re.compile(
    r"<untrusted(?:\s[^>]*)?>|</untrusted>",
    re.IGNORECASE,
)
_UNTRUSTED_NOTE_RE = re.compile(
    r"Content inside <untrusted>.*?(?:\n|$)",
    re.IGNORECASE,
)


def _alias_raw_key(key: str) -> str | None:
    k = str(key)
    if k in _RAW_KEY_ALIASES:
        return _RAW_KEY_ALIASES[k]
    lower = k.lower()
    if "faithfulness" in lower:
        return "faithfulness"
    if "relevanc" in lower and "context" not in lower:
        return "answer_relevancy"
    if "context_recall" in lower or lower.endswith("context_recall"):
        return "context_recall"
    if "context_precision" in lower:
        return "context_precision"
    if "correctness" in lower:
        return "answer_correctness"
    return None


def sanitize_context_chunk(text: str) -> str:
    """Strip <untrusted> wrappers / security notes so RAGAS sees body text."""
    if not text:
        return ""
    cleaned = _UNTRUSTED_NOTE_RE.sub("", text)
    cleaned = _UNTRUSTED_RE.sub("", cleaned)
    return cleaned.strip()


def sanitize_contexts(contexts: list[str]) -> list[str]:
    out = [sanitize_context_chunk(c) for c in contexts or []]
    return [c for c in out if c]


def has_ground_truth(row: dict) -> bool:
    """Cases with expected_behavior and/or gold source tags qualify as GT."""
    if (row.get("ground_truth") or "").strip():
        return True
    if (row.get("expected_behavior") or "").strip() and (
        row.get("gold_sources") or row.get("gold_context_source")
    ):
        return True
    # Soft: expected_behavior alone is still a usable reference proxy
    return bool((row.get("expected_behavior") or "").strip())


def build_reference(row: dict) -> str:
    """Proxy ground_truth / reference for retrieval + correctness metrics."""
    if (row.get("ground_truth") or "").strip():
        return str(row["ground_truth"]).strip()
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
    bundle: dict[str, Any] = {k: None for k in RAGAS_METRIC_KEYS}
    bundle.update(extra)
    return bundle


_CLIENTS: tuple[Any, Any] | None = None


def _ensure_asyncio_loop() -> None:
    """RAGAS opens async httpx clients; keep a live loop for long harness runs."""
    import asyncio

    try:
        import nest_asyncio

        nest_asyncio.apply()
    except ImportError:
        pass
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


def _gateway_ragas_clients():
    """Judge LLM + embeddings through app config (gateway / OpenAI-compatible)."""
    global _CLIENTS
    if _CLIENTS is not None:
        return _CLIENTS

    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper

    from app.config import gateway_api_key, openai_api_key, settings

    judge = ChatOpenAI(
        model=settings.judge_model,
        api_key=gateway_api_key() or openai_api_key(),
        base_url=settings.ai_gateway_base_url,
        temperature=0,
    )
    # Embeddings: prefer gateway when keyed, else direct OpenAI (same as app RAG).
    emb_kwargs: dict[str, Any] = {
        "model": "text-embedding-3-small",
        "api_key": openai_api_key() or gateway_api_key(),
    }
    if gateway_api_key() and not openai_api_key():
        emb_kwargs["base_url"] = settings.ai_gateway_base_url
        emb_kwargs["api_key"] = gateway_api_key()
    embeddings = OpenAIEmbeddings(**emb_kwargs)
    _CLIENTS = (
        LangchainLLMWrapper(judge),
        LangchainEmbeddingsWrapper(embeddings),
    )
    return _CLIENTS


def ragas_scores(row: dict, reply: str, contexts: list[str]) -> dict | None:
    """Run the RAGAS suite for one case. Returns None for non-RAG categories."""
    if row.get("category") not in RAG_CATEGORIES:
        return None
    if row.get("category") == "kb_retrieval" and "crypto" in row.get("input", "").lower():
        return _empty_metric_bundle(skipped="oos_negative_case")

    clean_contexts = sanitize_contexts(contexts)
    if not clean_contexts:
        return _empty_metric_bundle(
            skipped="no retrieved context",
            contexts_empty=True,
        )

    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_correctness,
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except ImportError as exc:
        return _empty_metric_bundle(skipped=f"ragas import failed: {exc}"[:180])

    with_gt = has_ground_truth(row)
    reference = build_reference(row) if with_gt else ""

    try:
        _ensure_asyncio_loop()
        ragas_llm, ragas_embeddings = _gateway_ragas_clients()
        dataset = Dataset.from_dict({
            "user_input": [row["input"]],
            "response": [reply],
            "retrieved_contexts": [list(clean_contexts)],
            "reference": [reference or ""],
            # v1 aliases
            "question": [row["input"]],
            "answer": [reply],
            "contexts": [list(clean_contexts)],
            "ground_truth": [reference or ""],
        })
        metrics: list[Any] = [faithfulness, answer_relevancy]
        if with_gt and reference.strip():
            metrics.extend([context_precision, context_recall, answer_correctness])

        result: Any = evaluate(
            dataset,
            metrics=metrics,
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            raise_exceptions=False,
        )
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
        bundle = _empty_metric_bundle(
            contexts_empty=False,
            n_contexts=len(clean_contexts),
            used_ground_truth=with_gt,
        )
        bundle.update(normalized)
        if not with_gt:
            for key in RAGAS_GT_KEYS:
                bundle.setdefault(key, None)
            bundle["gt_skipped"] = True
        if not any(isinstance(bundle.get(k), (int, float)) for k in RAGAS_METRIC_KEYS):
            bundle["error"] = "ragas returned no numeric scores"
            bundle["raw_keys"] = sorted(str(k) for k in raw.keys())[:20]
        return bundle
    except Exception as exc:
        return _empty_metric_bundle(error=str(exc)[:240], contexts_empty=False)


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


def empty_context_case_ids(results: list[dict]) -> list[int]:
    """RAG cases where retrieval returned nothing (retrieval bug signal)."""
    ids: list[int] = []
    for r in results:
        if r.get("category") not in RAG_CATEGORIES:
            continue
        ragas = r.get("ragas") if isinstance(r.get("ragas"), dict) else {}
        # Intentional negative / skipped cases are not retrieval bugs.
        skipped = str(ragas.get("skipped") or "")
        if skipped in {"oos_negative_case"} or skipped.startswith("ragas import"):
            continue
        contexts = r.get("contexts") or []
        if (
            ragas.get("contexts_empty")
            or skipped == "no retrieved context"
            or (ragas is not None and not sanitize_contexts(contexts) and skipped)
        ):
            try:
                ids.append(int(r["id"]))
            except (KeyError, TypeError, ValueError):
                pass
    return ids

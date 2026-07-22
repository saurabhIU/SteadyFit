"""Lightweight per-call LLM usage logging (Gateway credit visibility)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("steadyfit.usage")


def extract_usage(response: Any) -> dict[str, int | None]:
    """Pull token counts from a LangChain AIMessage / OpenAI-style response."""
    usage: dict[str, Any] = {}
    meta = getattr(response, "usage_metadata", None)
    if isinstance(meta, dict):
        usage = meta
    else:
        resp_meta = getattr(response, "response_metadata", None) or {}
        if isinstance(resp_meta, dict):
            usage = resp_meta.get("token_usage") or resp_meta.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}
    prompt = usage.get("input_tokens", usage.get("prompt_tokens"))
    completion = usage.get("output_tokens", usage.get("completion_tokens"))
    total = usage.get("total_tokens")
    if total is None and prompt is not None and completion is not None:
        try:
            total = int(prompt) + int(completion)
        except (TypeError, ValueError):
            total = None
    return {
        "prompt_tokens": int(prompt) if prompt is not None else None,
        "completion_tokens": int(completion) if completion is not None else None,
        "total_tokens": int(total) if total is not None else None,
    }


def log_llm_usage(
    call_name: str,
    *,
    model: str,
    usage: dict[str, int | None] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structured log line for cost monitoring. Returns the payload logged."""
    payload: dict[str, Any] = {
        "call": call_name,
        "model": model,
        "prompt_tokens": (usage or {}).get("prompt_tokens"),
        "completion_tokens": (usage or {}).get("completion_tokens"),
        "total_tokens": (usage or {}).get("total_tokens"),
    }
    if extra:
        payload.update(extra)
    logger.info(
        "llm_usage call=%s model=%s prompt_tokens=%s completion_tokens=%s "
        "total_tokens=%s extra=%s",
        payload["call"],
        payload["model"],
        payload["prompt_tokens"],
        payload["completion_tokens"],
        payload["total_tokens"],
        {k: v for k, v in payload.items() if k not in {
            "call", "model", "prompt_tokens", "completion_tokens", "total_tokens",
        }},
    )
    return payload

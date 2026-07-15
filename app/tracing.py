"""LangSmith tracing helpers — best-effort, never required for chat.

Supports both LANGSMITH_* and legacy LANGCHAIN_* env vars. When tracing is
disabled or the key is missing, decorators and metadata are no-ops.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from langchain_core.runnables import RunnableConfig

logger = logging.getLogger("steadyfit.tracing")


def configure_tracing() -> None:
    """Load .env into os.environ and normalize LangSmith settings.

    Pydantic Settings ignores LANGCHAIN_*/LANGSMITH_* extras, so the SDK
    only sees them if they are present in the process environment.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
    except ImportError:
        pass

    # Prefer modern LANGSMITH_* names; mirror into LANGCHAIN_* for the SDK.
    if os.getenv("LANGSMITH_TRACING") and not os.getenv("LANGCHAIN_TRACING_V2"):
        os.environ["LANGCHAIN_TRACING_V2"] = os.environ["LANGSMITH_TRACING"]
    if os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_API_KEY"] = os.environ["LANGSMITH_API_KEY"]
    if os.getenv("LANGSMITH_PROJECT") and not os.getenv("LANGCHAIN_PROJECT"):
        os.environ["LANGCHAIN_PROJECT"] = os.environ["LANGSMITH_PROJECT"]
    # Default project when tracing is on but unset
    if _tracing_enabled() and not os.getenv("LANGCHAIN_PROJECT"):
        os.environ["LANGCHAIN_PROJECT"] = "steadyfit"

    if _tracing_enabled():
        logger.info(
            "langsmith_tracing_on project=%s",
            os.getenv("LANGCHAIN_PROJECT") or os.getenv("LANGSMITH_PROJECT"),
        )
    else:
        logger.info("langsmith_tracing_off")


def _tracing_enabled() -> bool:
    flag = (
        os.getenv("LANGCHAIN_TRACING_V2")
        or os.getenv("LANGSMITH_TRACING")
        or ""
    ).strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        return False
    return bool(os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY"))


def thread_run_config(
    thread_id: str,
    *,
    user_id: str | None = None,
    endpoint: str | None = None,
) -> RunnableConfig:
    """LangGraph invoke config with optional LangSmith metadata/tags."""
    cfg: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    if user_id or endpoint:
        meta: dict[str, Any] = {}
        if user_id:
            meta["user_id"] = user_id
        if endpoint:
            meta["endpoint"] = endpoint
        cfg["metadata"] = meta
        if user_id:
            cfg["tags"] = [user_id]
    return cfg


def annotate_run(**fields: Any) -> None:
    """Best-effort attach fields onto the current LangSmith run."""
    try:
        from langsmith import get_current_run_tree

        rt = get_current_run_tree()
        if rt is None:
            return
        for key, value in fields.items():
            if value is None:
                continue
            try:
                setattr(rt, key, value)
            except Exception:
                pass
        extras = {k: v for k, v in fields.items() if k not in {"outputs", "inputs", "name"}}
        if extras and hasattr(rt, "extra"):
            try:
                rt.extra = {**(rt.extra or {}), **extras}
            except Exception:
                pass
    except Exception:
        logger.debug("annotate_run skipped", exc_info=True)


def kb_retriever_outputs(outputs: Any) -> dict[str, Any]:
    """Shrink (chunks, citations) for the LangSmith UI."""
    if isinstance(outputs, tuple) and len(outputs) >= 2:
        _chunks, cites = outputs[0], outputs[1]
        sources = []
        for c in cites or []:
            if not isinstance(c, dict):
                continue
            sources.append({
                "source_file": c.get("source_file"),
                "kb_id": c.get("kb_id"),
                "section": c.get("section"),
                "tag": c.get("tag"),
                "score": c.get("score"),
            })
        return {"n_chunks": len(_chunks or []), "sources": sources}
    return {"raw_type": type(outputs).__name__}


def personal_retriever_outputs(outputs: Any) -> dict[str, Any]:
    if not isinstance(outputs, list):
        return {"n_chunks": 0}
    sources: list[str] = []
    for chunk in outputs:
        text = str(chunk)
        # Prefer [doc:source] prefix when present
        if "[doc:" in text:
            try:
                start = text.index("[doc:") + 5
                end = text.index("]", start)
                sources.append(text[start:end])
            except ValueError:
                sources.append("(parse_error)")
        elif "[doc:error]" in text or "error" in text.lower()[:40]:
            sources.append("(error)")
    return {"n_chunks": len(outputs), "sources": sources[:20]}


def memory_retriever_outputs(outputs: Any) -> dict[str, Any]:
    if isinstance(outputs, tuple) and len(outputs) >= 2:
        chunks, cites = outputs[0], outputs[1]
        return {
            "n_chunks": len(chunks or []),
            "sources": [
                {
                    "source_file": c.get("source_file"),
                    "tag": c.get("tag"),
                    "kind": c.get("kind"),
                }
                for c in (cites or [])
                if isinstance(c, dict)
            ],
        }
    return {"n_chunks": 0}


def exercise_tool_outputs(outputs: Any) -> dict[str, Any]:
    if isinstance(outputs, list):
        return {
            "n_hits": len(outputs),
            "ids": [ex.get("id") for ex in outputs[:25] if isinstance(ex, dict)],
            "names": [ex.get("name") for ex in outputs[:25] if isinstance(ex, dict)],
        }
    if isinstance(outputs, dict):
        return {"id": outputs.get("id"), "name": outputs.get("name")}
    return {"type": type(outputs).__name__}

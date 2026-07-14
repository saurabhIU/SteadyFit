"""Agentic tool-calling loop: LLM emits tool_calls → execute → continue."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.config import get_llm
from app.security import as_text

logger = logging.getLogger("steadyfit.tools")

MAX_TOOL_ROUNDS = 5


@dataclass
class ToolAgentResult:
    """Final assistant text plus raw tool outputs for RAG / debugging."""
    text: str
    tool_outputs: list[str] = field(default_factory=list)
    tools_called: list[str] = field(default_factory=list)


def run_tool_agent(
    *,
    system: str,
    user: str,
    tools: list[BaseTool],
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> ToolAgentResult:
    """Bind tools and loop until the model answers without tool_calls."""
    if not tools:
        llm = get_llm()
        reply = llm.invoke([
            SystemMessage(content=system),
            HumanMessage(content=user),
        ])
        return ToolAgentResult(text=as_text(reply.content))

    llm = get_llm().bind_tools(tools)
    tool_map = {t.name: t for t in tools}
    messages: list = [
        SystemMessage(content=system),
        HumanMessage(content=user),
    ]
    outputs: list[str] = []
    called: list[str] = []

    for _ in range(max_rounds):
        ai: AIMessage = llm.invoke(messages)  # type: ignore[assignment]
        messages.append(ai)
        tool_calls = getattr(ai, "tool_calls", None) or []
        if not tool_calls:
            return ToolAgentResult(
                text=as_text(ai.content),
                tool_outputs=outputs,
                tools_called=called,
            )

        for call in tool_calls:
            name = call.get("name") or ""
            args = call.get("args") or {}
            call_id = call.get("id") or name
            tool = tool_map.get(name)
            if tool is None:
                content = f"Unknown tool: {name}"
                logger.warning("unknown_tool name=%s", name)
            else:
                try:
                    raw = tool.invoke(args)
                    content = raw if isinstance(raw, str) else str(raw)
                except Exception as exc:
                    content = f"Tool error ({name}): {exc}"
                    logger.exception("tool_failed name=%s", name)
                called.append(name)
                outputs.append(content)
            messages.append(ToolMessage(content=content, tool_call_id=call_id))

    # Hit round limit — ask for a final answer without tools.
    final = get_llm().invoke(messages + [
        HumanMessage(content="Stop calling tools. Give your final answer now."),
    ])
    return ToolAgentResult(
        text=as_text(final.content),
        tool_outputs=outputs,
        tools_called=called,
    )

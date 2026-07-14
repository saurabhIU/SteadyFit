"""Unit tests for agentic tool-calling loop (mocked LLM)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from app.graph.tool_agent import run_tool_agent


@tool
def add(a: int, b: int) -> str:
    """Add two integers and return the sum as a string."""
    return str(a + b)


def test_run_tool_agent_executes_tool_calls_then_answers():
    first = AIMessage(
        content="",
        tool_calls=[{"name": "add", "args": {"a": 2, "b": 3}, "id": "call-1", "type": "tool_call"}],
    )
    second = AIMessage(content="The sum is 5.")

    mock_bound = MagicMock()
    mock_bound.invoke.side_effect = [first, second]
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_bound

    with patch("app.graph.tool_agent.get_llm", return_value=mock_llm):
        result = run_tool_agent(
            system="You are a calculator.",
            user="What is 2+3?",
            tools=[add],
        )

    assert result.text == "The sum is 5."
    assert result.tools_called == ["add"]
    assert result.tool_outputs == ["5"]
    # First invoke asked for a tool; second message list included a ToolMessage.
    second_call_msgs = mock_bound.invoke.call_args_list[1].args[0]
    assert any(isinstance(m, ToolMessage) for m in second_call_msgs)


def test_run_tool_agent_no_tools_skips_bind():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = SimpleNamespace(content="hello")

    with patch("app.graph.tool_agent.get_llm", return_value=mock_llm):
        result = run_tool_agent(system="sys", user="hi", tools=[])

    assert result.text == "hello"
    mock_llm.bind_tools.assert_not_called()

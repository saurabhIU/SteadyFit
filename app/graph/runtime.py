"""LangGraph runtime helpers."""
from langchain_core.runnables import RunnableConfig


def thread_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id}}

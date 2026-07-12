"""Tavily web search tool (public data requirement)."""
from app.config import settings


def web_search(query: str, k: int = 3) -> list[str]:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)
        res = client.search(query, max_results=k)
        return [f"[web:{r['url']}] {r['content']}" for r in res.get("results", [])]
    except Exception as e:
        return [f"[web:error] search unavailable: {e}"]

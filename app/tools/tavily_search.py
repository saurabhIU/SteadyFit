"""Tavily web search tool (public data requirement)."""
from app.config import settings
from app.security import safe_tool_error, wrap_untrusted


def web_search(query: str, k: int = 3) -> list[str]:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)
        res = client.search(query, max_results=k)
        return [
            wrap_untrusted(f"[web:{r['url']}] {r['content']}", source="web")
            for r in res.get("results", [])
        ]
    except Exception:
        return [safe_tool_error("web")]

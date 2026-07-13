"""Central config. All chat models go through the Vercel AI Gateway."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM gateway (Vercel AI Gateway — OpenAI-compatible Chat Completions API)
    ai_gateway_api_key: str = ""
    ai_gateway_base_url: str = "https://ai-gateway.vercel.sh/v1"
    primary_model: str = "anthropic/claude-sonnet-4.5"
    judge_model: str = "openai/gpt-4o-mini"
    openai_api_key: str = ""          # embeddings only
    tavily_api_key: str = ""
    usda_api_key: str = ""
    # Postgres (Neon): vector store + LangGraph checkpointer
    database_url: str = ""
    # Shared secret for the external cron that triggers the weekly review
    internal_cron_secret: str = ""
    # Vercel frontend origin for CORS (localhost is always allowed for dev)
    frontend_url: str = ""
    profile_db: str = "data/profile.sqlite"
    # Blast-radius / input caps
    max_message_length: int = 2000
    llm_max_tokens: int = 1024
    chat_rate_limit: str = "20/minute"

    class Config:
        env_file = ".env"
        extra = "ignore"  # .env also carries LANGCHAIN_* vars for LangSmith


settings = Settings()


def gateway_api_key() -> str:
    """Vercel AI Gateway key; falls back to VERCEL_OIDC_TOKEN on Vercel deploys."""
    return settings.ai_gateway_api_key or os.environ.get("VERCEL_OIDC_TOKEN", "")


@lru_cache
def get_llm(
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.3,
):
    """LLM via the Vercel AI Gateway (requirement: use an LLM gateway)."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model or settings.primary_model,
        api_key=gateway_api_key,
        base_url=settings.ai_gateway_base_url,
        temperature=temperature,
        max_tokens=max_tokens if max_tokens is not None else settings.llm_max_tokens,
    )

"""LangChain @tool wrappers — models choose these via bind_tools / tool_calls."""
from __future__ import annotations

import json

from langchain_core.tools import tool

from app.memory.store import get_adherence_stats
from app.rag.retriever import retrieve_personal
from app.tools.calendar_tool import get_calendar_conflicts
from app.tools.food_api import lookup_food
from app.tools.tavily_search import web_search


@tool
def calendar_conflicts() -> str:
    """Read the user's calendar busy blocks / conflicts for this week.
    Call this before proposing any schedule changes."""
    return json.dumps(get_calendar_conflicts())


@tool
def usda_food_lookup(query: str) -> str:
    """Look up calorie and macronutrient facts from USDA FoodData Central.
    Pass a short food name or meal description (e.g. 'biryani', 'mango lassi')."""
    return "\n".join(lookup_food(query))


@tool
def retrieve_personal_docs(query: str) -> str:
    """Semantic search over the user's uploaded fitness documents
    (programs, guidelines PDFs, recipes) stored in the vector database.
    Use for questions about their own program or curated guidelines corpus."""
    chunks = retrieve_personal(query, k=4)
    return "\n\n".join(chunks) if chunks else "[doc] no matching chunks"


@tool
def retrieve_recipes(query: str) -> str:
    """Search the user's uploaded recipe collection for meal ideas matching the query."""
    chunks = retrieve_personal(query, collection_filter="recipes", k=3)
    return "\n\n".join(chunks) if chunks else "[doc] no matching recipes"


@tool
def web_search_fitness(query: str) -> str:
    """Search the public web (Tavily) for current fitness, nutrition, or
    supplement facts that are not in the user's personal documents."""
    hits = web_search(query)
    return "\n\n".join(hits) if hits else "[web] no results"


@tool
def adherence_stats() -> str:
    """Fetch the user's adherence stats: streaks, recent skips, logging gaps.
    Call this before deciding if drop-off RISK is present."""
    return json.dumps(get_adherence_stats())


SCHEDULER_TOOLS = [calendar_conflicts]
NUTRITION_TOOLS = [usda_food_lookup, retrieve_recipes]
KNOWLEDGE_TOOLS = [retrieve_personal_docs, web_search_fitness]
ADHERENCE_TOOLS = [adherence_stats]

# Tool names whose outputs should feed retrieved_context for citations.
RAG_TOOL_NAMES = {"retrieve_personal_docs", "retrieve_recipes", "web_search_fitness"}

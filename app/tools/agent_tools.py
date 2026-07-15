"""LangChain @tool wrappers — models choose these via bind_tools / tool_calls."""
from __future__ import annotations

import json

from langchain_core.tools import tool

from app.memory.store import get_adherence_stats
from app.rag.retriever import retrieve_kb, retrieve_personal
from app.tools.calendar_tool import get_calendar_conflicts
from app.tools.exercise_lookup import find_exercises, get_substitutions
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
    """Semantic search over the user's uploaded personal documents only
    (programs, recipes) — not the shared SteadyFit knowledge base."""
    chunks = retrieve_personal(query, k=4)
    return "\n\n".join(chunks) if chunks else "[doc] no matching chunks"


@tool
def retrieve_recipes(query: str) -> str:
    """Search the user's uploaded recipe collection for meal ideas matching the query."""
    chunks = retrieve_personal(query, collection_filter="recipes", k=3)
    return "\n\n".join(chunks) if chunks else "[doc] no matching recipes"


@tool
def retrieve_kb_docs(query: str, modality: str = "") -> str:
    """Semantic search over the curated SteadyFit knowledge base
    (exercises, guides, templates, nutrition/exercise science).
    Use for technique, form, programs, and science explanations.
    Optional modality filter: gym, home, hotel, etc."""
    chunks, _cites = retrieve_kb(query, modality=modality or None, k=5)
    return "\n\n".join(chunks) if chunks else "[kb] no matching chunks"


@tool
def retrieve_nutrition_science(query: str) -> str:
    """Retrieve SteadyFit nutrition science KB sections (macros, meal ideas, eating out)."""
    chunks, _ = retrieve_kb(query, doc_types=["kb_science"], k=4)
    return "\n\n".join(chunks) if chunks else "[kb] no nutrition science chunks"


@tool
def web_search_fitness(query: str) -> str:
    """Search the public web (Tavily) for current fitness/product facts.
    Prefer retrieve_kb_docs for technique and SteadyFit science."""
    hits = web_search(query)
    return "\n\n".join(hits) if hits else "[web] no results"


@tool
def adherence_stats() -> str:
    """Fetch the user's adherence stats: streaks, recent skips, logging gaps.
    Call this before deciding if drop-off RISK is present."""
    return json.dumps(get_adherence_stats())


@tool
def find_exercises_tool(
    muscle: str = "",
    modality: str = "",
    difficulty_max: str = "intermediate",
    equipment_csv: str = "",
    exclude_contraindications_csv: str = "",
) -> str:
    """STRUCTURED lookup (no embeddings) — prefer for SELECTING exercises.
    Filter by muscle (e.g. chest, quad), modality (gym/home/hotel), max difficulty,
    optional equipment list (comma-separated), and contraindications to exclude
    (comma-separated, e.g. knee, shoulder)."""
    equipment = [e.strip() for e in equipment_csv.split(",") if e.strip()] if equipment_csv else None
    # empty string equipment_csv with hotel/home → treat as no equipment
    if modality in {"home", "hotel", "office"} and equipment_csv == "":
        equipment = []
    excl = [e.strip() for e in exclude_contraindications_csv.split(",") if e.strip()]
    hits = find_exercises(
        muscle=muscle or None,
        equipment_available=equipment,
        modality=modality or None,
        difficulty_max=difficulty_max or None,
        exclude_contraindications=excl or None,
    )
    slim = [
        {
            "id": h.get("id"),
            "name": h.get("name"),
            "difficulty": h.get("difficulty"),
            "modality": h.get("modality"),
            "equipment": h.get("equipment"),
            "contraindications": h.get("contraindications"),
        }
        for h in hits[:20]
    ]
    return json.dumps(slim)


@tool
def get_exercise_substitutions(exercise_id: str, constraint: str) -> str:
    """STRUCTURED substitutions for an exercise kb_id under a constraint key
    (e.g. home_only, no_barbell, shoulder_pain, beginner). Prefer this over inventing names."""
    hits = get_substitutions(exercise_id, constraint)
    slim = [{"id": h.get("id"), "name": h.get("name"), "modality": h.get("modality")} for h in hits]
    return json.dumps(slim)


SCHEDULER_TOOLS = [
    calendar_conflicts,
    find_exercises_tool,
    get_exercise_substitutions,
    retrieve_kb_docs,
]
NUTRITION_TOOLS = [usda_food_lookup, retrieve_recipes, retrieve_nutrition_science]
KNOWLEDGE_TOOLS = [retrieve_personal_docs, retrieve_kb_docs, web_search_fitness]
ADHERENCE_TOOLS = [adherence_stats]

RAG_TOOL_NAMES = {
    "retrieve_personal_docs",
    "retrieve_recipes",
    "retrieve_kb_docs",
    "retrieve_nutrition_science",
    "web_search_fitness",
}

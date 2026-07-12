"""Nutrition agent: works with what the user actually ate."""
from app.config import get_llm
from app.graph.state import CouncilState
from app.tools.food_api import lookup_food
from app.rag.retriever import retrieve_personal

SYSTEM = """You are the Nutrition agent for everyday people. No rigid meal plans.
When the user logs real food (including eating out), estimate macros, adjust the rest
of the day/week, and stay non-judgmental. Prefer recipes from the user's own uploaded
collection when relevant. Verify macro claims with the food database results provided."""


def nutrition_node(state: CouncilState) -> dict:
    user_msg = state.messages[-1].content if state.messages else ""
    recipes = retrieve_personal(user_msg, collection_filter="recipes", k=3)
    food_facts = lookup_food(user_msg)
    llm = get_llm()
    prompt = (
        f"Profile: {state.profile.model_dump_json()}\n"
        f"Targets: {state.week_plan.model_dump_json() if state.week_plan else 'none'}\n"
        f"User's own recipes (RAG): {recipes}\nUSDA lookup: {food_facts}\n"
        f"User said: {user_msg}"
    )
    proposal = llm.invoke([{"role": "system", "content": SYSTEM},
                           {"role": "user", "content": prompt}]).content
    return {
        "proposals": {**state.proposals, "nutrition": proposal},
        "retrieved_context": state.retrieved_context + recipes,
    }

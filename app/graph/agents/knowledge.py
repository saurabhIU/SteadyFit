"""Knowledge agent: agentic RAG — decide between personal docs (Qdrant) and web (Tavily)."""
from app.config import get_llm
from app.graph.state import CouncilState
from app.rag.retriever import retrieve_personal
from app.tools.tavily_search import web_search

ROUTER_SYSTEM = """Decide where the answer lives. Reply with exactly one word:
- personal : the user's own program, recipes, or logs ("my program", "my recipes")
- web      : public/current facts (supplement safety, exercise science, anything time-sensitive)
- both     : needs the user's docs AND public verification"""


def knowledge_node(state: CouncilState) -> dict:
    q = state.messages[-1].content if state.messages else ""
    llm = get_llm()
    route = llm.invoke([{"role": "system", "content": ROUTER_SYSTEM},
                        {"role": "user", "content": q}]).content.strip().lower()
    context: list[str] = []
    if route in ("personal", "both"):
        context += retrieve_personal(q, k=4)
    if route in ("web", "both"):
        context += web_search(q)
    return {
        "retrieved_context": state.retrieved_context + context,
        "proposals": {**state.proposals, "knowledge": f"route={route}, {len(context)} chunks"},
    }

"""Builds the SteadyFit coaching council graph.

Topology:
    coach (supervisor) -> {scheduler | nutrition | adherence | rag}
    specialists -> council
    council -> coach   (if conflict, e.g. risk_flag while plan got denser)
    council -> approve (human-in-the-loop interrupt, if plan changed)
    council -> END     (informational answer)
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection
from psycopg.rows import dict_row

from app.config import settings
from app.graph.state import CouncilState
from app.graph.supervisor import coach_node, council_node, approve_node
from app.graph.agents.scheduler import scheduler_node
from app.graph.agents.nutrition import nutrition_node
from app.graph.agents.adherence import adherence_node
from app.graph.agents.knowledge import knowledge_node

MAX_COUNCIL_ROUNDS = 2


def route_from_coach(state: CouncilState) -> str:
    return state.intent or "knowledge"


def route_from_council(state: CouncilState) -> str:
    if state.risk_flag and state.council_rounds < MAX_COUNCIL_ROUNDS:
        return "coach"          # renegotiate: simplify the plan
    if state.proposals.get("plan_changed"):
        return "approve"        # human-in-the-loop
    return "end"


def build_graph():
    g = StateGraph(CouncilState)

    g.add_node("coach", coach_node)
    g.add_node("scheduler", scheduler_node)
    g.add_node("nutrition", nutrition_node)
    g.add_node("adherence", adherence_node)
    g.add_node("knowledge", knowledge_node)   # agentic RAG: personal docs vs Tavily
    g.add_node("council", council_node)
    g.add_node("approve", approve_node)       # uses langgraph interrupt()

    g.set_entry_point("coach")
    g.add_conditional_edges("coach", route_from_coach, {
        "schedule": "scheduler",
        "nutrition": "nutrition",
        "adherence": "adherence",
        "knowledge": "knowledge",
    })
    for node in ("scheduler", "nutrition", "adherence", "knowledge"):
        g.add_edge(node, "council")
    g.add_conditional_edges("council", route_from_council, {
        "coach": "coach",
        "approve": "approve",
        "end": END,
    })
    g.add_edge("approve", END)

    # Long-lived connection; connection kwargs per langgraph-checkpoint-postgres docs.
    conn = Connection.connect(
        settings.database_url,
        autocommit=True,
        prepare_threshold=0,
        row_factory=dict_row,
    )
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()  # idempotent schema migration, runs at app startup
    return g.compile(checkpointer=checkpointer)

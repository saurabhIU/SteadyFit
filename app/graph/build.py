"""Builds the SteadyFit AI Coaching Team graph.

Topology:
    coach (supervisor) -> {scheduler | nutrition | adherence | rag}
    specialists -> coaching_team
    coaching_team -> coach   (if conflict, e.g. risk_flag while plan got denser)
    coaching_team -> approve (human-in-the-loop interrupt, if plan changed)
    coaching_team -> END     (informational answer)
"""
from typing import cast

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph
from psycopg import Connection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool

from app.config import settings
from app.graph.agents.adherence import adherence_node
from app.graph.agents.knowledge import knowledge_node
from app.graph.agents.nutrition import nutrition_node
from app.graph.agents.scheduler import scheduler_node
from app.graph.state import CoachingTeamState
from app.graph.supervisor import approve_node, coach_node, coaching_team_node

MAX_COACHING_TEAM_ROUNDS = 2

DictConnectionPool = ConnectionPool[Connection[DictRow]]

# Keep the pool for the process lifetime. A single long-lived Connection dies when
# Neon/Render idle-timeouts it; the pool checks and replaces dead conns.
_pool: DictConnectionPool | None = None


def get_checkpointer_pool() -> DictConnectionPool:
    global _pool
    if _pool is None:
        # Runtime uses dict_row; constructor generics default to TupleRow for the checker.
        _pool = cast(
            DictConnectionPool,
            ConnectionPool(
                conninfo=settings.database_url,
                min_size=1,
                max_size=5,
                # Recycle before typical Neon idle kills (~5m); health-check on checkout.
                max_idle=120,
                max_lifetime=1800,
                kwargs={
                    "autocommit": True,
                    "prepare_threshold": 0,
                    "row_factory": dict_row,
                },
                check=ConnectionPool.check_connection,
                open=True,
            ),
        )
    return _pool


def close_checkpointer_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def route_from_coach(state: CoachingTeamState) -> str:
    return state.intent or "knowledge"


def route_from_coaching_team(state: CoachingTeamState) -> str:
    if state.risk_flag and state.coaching_team_rounds < MAX_COACHING_TEAM_ROUNDS:
        return "coach"          # renegotiate: simplify the plan
    if state.proposals.get("plan_changed"):
        return "approve"        # human-in-the-loop
    return "end"


def build_graph():
    g = StateGraph(CoachingTeamState)

    g.add_node("coach", coach_node)
    g.add_node("scheduler", scheduler_node)
    g.add_node("nutrition", nutrition_node)
    g.add_node("adherence", adherence_node)
    g.add_node("knowledge", knowledge_node)   # agentic RAG: personal docs vs Tavily
    g.add_node("coaching_team", coaching_team_node)
    g.add_node("approve", approve_node)       # uses langgraph interrupt()

    g.set_entry_point("coach")
    g.add_conditional_edges("coach", route_from_coach, {
        "schedule": "scheduler",
        "nutrition": "nutrition",
        "adherence": "adherence",
        "knowledge": "knowledge",
    })
    for node in ("scheduler", "nutrition", "adherence", "knowledge"):
        g.add_edge(node, "coaching_team")
    g.add_conditional_edges("coaching_team", route_from_coaching_team, {
        "coach": "coach",
        "approve": "approve",
        "end": END,
    })
    g.add_edge("approve", END)

    pool = get_checkpointer_pool()
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()  # idempotent schema migration, runs at app startup
    return g.compile(checkpointer=checkpointer)

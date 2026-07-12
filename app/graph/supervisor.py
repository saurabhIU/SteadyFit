"""Coach (supervisor), council (negotiation), and approval nodes."""
from langgraph.types import interrupt
from app.config import get_llm
from app.graph.state import CouncilState, WeekPlan

COACH_SYSTEM = """You are the Head Coach of OneRepMax, a friendly fitness copilot for busy,
everyday people (not pro athletes). You supervise three specialists — Scheduler, Nutrition,
Adherence — and an agentic-RAG Knowledge tool over the user's own documents + web search.

Given the conversation and the user's profile, classify the request into exactly one intent:
- schedule   (planning, missed workouts, travel, moving sessions)
- nutrition  (food logged, meals, macros, recipes)
- adherence  (check-ins, motivation, streaks, weekly review)
- knowledge  (any question needing the user's documents or web facts)

If a previous council round flagged drop-off RISK, your job changes: SIMPLIFY the plan
(fewer/shorter sessions, easier meals). Be warm, concrete, never guilt-tripping.

Respond with just the intent word."""


def coach_node(state: CouncilState) -> dict:
    llm = get_llm()
    msgs = [{"role": "system", "content": COACH_SYSTEM}] + [
        m for m in state.messages
    ]
    intent = llm.invoke(msgs).content.strip().lower()
    if intent not in {"schedule", "nutrition", "adherence", "knowledge"}:
        intent = "knowledge"
    return {"intent": intent, "council_rounds": state.council_rounds + 1}


COUNCIL_SYSTEM = """You are the Head Coach reviewing your specialists' proposals before
answering the user. Merge proposals into one clear, warm reply. If the adherence agent
flagged risk AND the proposed plan got harder, do not answer — signal renegotiation instead.
Cite sources for any retrieved facts using [source] tags found in the context."""


def council_node(state: CouncilState) -> dict:
    llm = get_llm()
    context = "\n\n".join(state.retrieved_context) if state.retrieved_context else "none"
    proposals = "\n".join(f"{k}: {v}" for k, v in state.proposals.items()) or "none"
    prompt = (
        f"User profile: {state.profile.model_dump_json()}\n"
        f"Current plan: {state.week_plan.model_dump_json() if state.week_plan else 'none'}\n"
        f"Retrieved context:\n{context}\n\nSpecialist proposals:\n{proposals}\n\n"
        f"Risk flag: {state.risk_flag}\n"
        "Write the final reply to the user."
    )
    reply = llm.invoke(
        [{"role": "system", "content": COUNCIL_SYSTEM},
         {"role": "user", "content": prompt}]
    )
    # Keep routing flags only — raw specialist text is merged into the reply above.
    retained = {
        k: state.proposals[k]
        for k in ("plan_changed", "proposed_week_plan")
        if k in state.proposals
    }
    return {"messages": [reply], "proposals": retained}


def approve_node(state: CouncilState) -> dict:
    """Human-in-the-loop: pause the graph until the user accepts/edits the plan change."""
    raw = state.proposals.get("proposed_week_plan")
    proposed_plan = WeekPlan(**raw) if isinstance(raw, dict) else state.week_plan
    decision = interrupt({
        "type": "plan_approval",
        "proposed_plan": proposed_plan.model_dump() if proposed_plan else None,
        "scheduler_summary": (state.proposals.get("scheduler") or "")[:600],
    })
    # decision arrives via Command(resume=...) from the API layer
    accepted = decision == "accept"
    note = (
        "Plan approved and saved — you're set for the week."
        if accepted
        else "No worries — kept your previous plan. Tell me if you want a different adjustment."
    )
    updates: dict = {
        "messages": [{"role": "assistant", "content": note}],
        "proposals": {},
    }
    if accepted and proposed_plan:
        updates["week_plan"] = proposed_plan
    return updates

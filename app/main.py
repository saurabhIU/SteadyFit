"""FastAPI backend: chat, uploads, weekly review. Frontend is the Next.js app in web/."""
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import BaseModel

from app.config import settings
from app.graph.build import build_graph
from app.graph.response import build_chat_payload, build_thread_history
from app.graph.runtime import thread_config
from app.memory.context import bootstrap_input, persist_approved_plan, plan_snapshot
from app.rag.ingest import ingest

graph: CompiledStateGraph | None = None


def require_graph() -> CompiledStateGraph:
    if graph is None:
        raise RuntimeError("Graph not initialized")
    return graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    Path("data").mkdir(exist_ok=True)
    graph = build_graph()
    yield


app = FastAPI(title="OneRepMax", lifespan=lifespan)

# Next.js on Vercel (or localhost:3000) calls this API cross-origin.
_origins = ["http://localhost:3000", "http://localhost:5173"]
if settings.frontend_url:
    _origins.append(settings.frontend_url.rstrip("/"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/internal/weekly-review")
def weekly_review(x_internal_secret: str | None = Header(default=None)):
    """The autonomous loop: agents convene without a user prompt.

    Called by an external cron (Render Cron Job), authenticated with a
    shared secret. Fails closed if the secret is unset.
    """
    if not settings.internal_cron_secret or x_internal_secret != settings.internal_cron_secret:
        raise HTTPException(status_code=401, detail="unauthorized")
    thread = "weekly-review"
    config = thread_config(thread)
    g = require_graph()
    result = g.invoke(
        bootstrap_input(
            g,
            thread,
            messages=[{
                "role": "user",
                "content": "SYSTEM_TRIGGER: run the weekly review and propose next week's plan.",
            }],
        ),
        config=config,
    )
    return {"ok": True, **build_chat_payload(thread, result, graph=g, config=config)}


class ChatIn(BaseModel):
    message: str
    thread_id: str | None = None


@app.post("/api/chat")
def chat(body: ChatIn):
    thread = body.thread_id or str(uuid.uuid4())
    config = thread_config(thread)
    g = require_graph()
    result = g.invoke(
        bootstrap_input(
            g,
            thread,
            messages=[{"role": "user", "content": body.message}],
        ),
        config=config,
    )
    return build_chat_payload(thread, result, graph=g, config=config)


@app.get("/api/chat/history")
def chat_history(thread_id: str):
    return build_thread_history(require_graph(), thread_id)


class ApproveIn(BaseModel):
    thread_id: str
    decision: Literal["accept", "reject"]


@app.post("/api/approve")
def approve(body: ApproveIn):
    config = thread_config(body.thread_id)
    g = require_graph()
    result = g.invoke(Command(resume=body.decision), config=config)
    if body.decision == "accept":
        persist_approved_plan(g, body.thread_id)
    return build_chat_payload(body.thread_id, result, graph=g, config=config)


@app.get("/api/plan")
def get_plan(thread_id: str | None = None):
    thread = thread_id or "default"
    return plan_snapshot(require_graph(), thread)


@app.post("/api/upload")
async def upload(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    dest = Path("data/uploads") / file.filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())
    n = ingest(str(dest))
    return {"ingested_chunks": n}

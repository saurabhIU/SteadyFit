"""FastAPI backend: chat, uploads, weekly review, multi-profile."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, cast

from fastapi import FastAPI, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.types import ExceptionHandler

from app.chat_pipeline import process_user_chat
from app.config import settings
from app.graph.build import build_graph, close_checkpointer_pool
from app.graph.response import build_chat_payload, build_thread_history
from app.graph.runtime import make_thread_id, thread_config, weekly_review_thread
from app.memory.context import bootstrap_input, persist_approved_plan, plan_snapshot
from app.memory.store import (
    create_user,
    list_users,
    reset_user,
    user_exists,
)
from app.memory.user_context import set_current_user_id
from app.rag.ingest import ingest

graph: CompiledStateGraph | None = None
limiter = Limiter(key_func=get_remote_address)


def require_graph() -> CompiledStateGraph:
    if graph is None:
        raise RuntimeError("Graph not initialized")
    return graph


def require_user_id(x_user_id: str | None) -> str:
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    uid = x_user_id.strip()
    if not user_exists(uid):
        raise HTTPException(status_code=404, detail=f"unknown profile: {uid}")
    set_current_user_id(uid)
    return uid


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    Path("data").mkdir(exist_ok=True)
    graph = build_graph()
    try:
        yield
    finally:
        close_checkpointer_pool()
        graph = None


app = FastAPI(title="SteadyFit", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    cast(ExceptionHandler, _rate_limit_exceeded_handler),
)

_origins = ["http://localhost:3000", "http://localhost:5173"]
if settings.frontend_url:
    for origin in settings.frontend_url.split(","):
        cleaned = origin.strip().rstrip("/")
        if cleaned:
            _origins.append(cleaned)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/profiles")
def api_list_profiles():
    return {"profiles": list_users()}


class CreateProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


@app.post("/api/profiles")
def api_create_profile(body: CreateProfileIn):
    uid = create_user(body.name.strip())
    return {"user_id": uid, "name": body.name.strip(), "onboarding_complete": False}


@app.post("/api/profiles/{user_id}/reset")
def api_reset_profile(user_id: str):
    if not user_exists(user_id):
        raise HTTPException(status_code=404, detail="unknown profile")
    reset_user(user_id)
    return {"ok": True, "user_id": user_id}


@app.post("/internal/weekly-review")
def weekly_review(x_internal_secret: str | None = Header(default=None)):
    """Run weekly review for every profile (cron)."""
    if not settings.internal_cron_secret or x_internal_secret != settings.internal_cron_secret:
        raise HTTPException(status_code=401, detail="unauthorized")
    g = require_graph()
    results = []
    for user in list_users():
        uid = user["user_id"]
        set_current_user_id(uid)
        thread = weekly_review_thread(uid)
        config = thread_config(thread)
        result = g.invoke(
            bootstrap_input(
                g,
                thread,
                user_id=uid,
                messages=[{
                    "role": "user",
                    "content": (
                        "SYSTEM_TRIGGER: run the weekly review and propose next week's plan."
                    ),
                }],
            ),
            config=config,
        )
        payload = build_chat_payload(thread, result, graph=g, config=config)
        results.append({"user_id": uid, **payload})
    return {"ok": True, "reviews": results}


class ChatIn(BaseModel):
    message: str
    thread_id: str | None = None


@app.post("/api/chat")
@limiter.limit(settings.chat_rate_limit)
def chat(
    request: Request,
    body: ChatIn,
    x_user_id: str | None = Header(default=None),
):
    uid = require_user_id(x_user_id)
    return process_user_chat(
        require_graph(),
        body.message,
        user_id=uid,
        thread_id=body.thread_id,
    )


@app.get("/api/chat/history")
def chat_history(
    thread_id: str,
    x_user_id: str | None = Header(default=None),
):
    uid = require_user_id(x_user_id)
    thread = make_thread_id(uid, thread_id)
    return build_thread_history(require_graph(), thread)


class ApproveIn(BaseModel):
    thread_id: str
    decision: Literal["accept", "reject"]


@app.post("/api/approve")
def approve(
    body: ApproveIn,
    x_user_id: str | None = Header(default=None),
):
    uid = require_user_id(x_user_id)
    thread = make_thread_id(uid, body.thread_id)
    config = thread_config(thread)
    g = require_graph()
    result = g.invoke(Command(resume=body.decision), config=config)
    if body.decision == "accept":
        persist_approved_plan(g, thread, uid)
    return build_chat_payload(thread, result, graph=g, config=config)


@app.get("/api/plan")
def get_plan(
    thread_id: str | None = None,
    x_user_id: str | None = Header(default=None),
):
    uid = require_user_id(x_user_id)
    thread = make_thread_id(uid, thread_id or "default")
    return plan_snapshot(require_graph(), thread, uid)


@app.post("/api/upload")
async def upload(
    file: UploadFile,
    x_user_id: str | None = Header(default=None),
):
    uid = require_user_id(x_user_id)
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    safe_name = Path(file.filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="invalid filename")
    dest = Path("data/uploads") / uid / safe_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())
    n = ingest(str(dest), user_id=uid)
    return {"ingested_chunks": n}

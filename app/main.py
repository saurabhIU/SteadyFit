"""FastAPI backend: chat, uploads, weekly review. Frontend is the Next.js app in web/."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal, cast
from fastapi import FastAPI, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.types import ExceptionHandler

from app.chat_pipeline import process_user_chat
from app.config import settings
from app.graph.build import build_graph, close_checkpointer_pool
from app.graph.response import build_chat_payload, build_thread_history
from app.graph.runtime import thread_config
from app.memory.context import bootstrap_input, persist_approved_plan, plan_snapshot
from app.rag.ingest import ingest

graph: CompiledStateGraph | None = None
limiter = Limiter(key_func=get_remote_address)


def require_graph() -> CompiledStateGraph:
    if graph is None:
        raise RuntimeError("Graph not initialized")
    return graph


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
# slowapi's handler is typed for RateLimitExceeded; Starlette expects Exception.
app.add_exception_handler(
    RateLimitExceeded,
    cast(ExceptionHandler, _rate_limit_exceeded_handler),
)

# Next.js on Vercel (or localhost:3000) calls this API cross-origin.
_origins = ["http://localhost:3000", "http://localhost:5173"]
if settings.frontend_url:
    for origin in settings.frontend_url.split(","):
        cleaned = origin.strip().rstrip("/")
        if cleaned:
            _origins.append(cleaned)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    # Vercel production + preview deploys (e.g. steadyfit.vercel.app, steadyfit-git-main-*.vercel.app)
    allow_origin_regex=r"https://.*\.vercel\.app",
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
@limiter.limit(settings.chat_rate_limit)
def chat(request: Request, body: ChatIn):
    return process_user_chat(require_graph(), body.message, body.thread_id)


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
    # Keep uploads as basename only — block path traversal.
    safe_name = Path(file.filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="invalid filename")
    dest = Path("data/uploads") / safe_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())
    n = ingest(str(dest))
    return {"ingested_chunks": n}

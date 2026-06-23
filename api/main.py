"""
Thin FastAPI chat layer — wires a traveler's message to that city's
Orchestrator, with three layers of memory (see data/conversation_store.py):
Chat History (full transcript), Session Memory (the recent-turns window fed
to the LLM), and User Memory (durable cross-session facts).

POST /chat/sessions                {"city_id", "user_id"}    -> {"session_id"}
POST /chat/message                 {"session_id", "message"} -> {"reply"}
GET  /chat/sessions/{id}/history                             -> [{"role", "content"}, ...]
GET  /map/markers?city_id=...                                -> [{"name","type","category","lat","lng"}, ...]
POST /admin/refresh         {"city_id","city_name","scope"}   -> {"status","scope", ...}
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.orchestrator import build_orchestrator
from data.conversation_store import ConversationStore
from data.ingestion_pipeline import DataIngestionPipeline
from data.repository import Repository

logger = logging.getLogger(__name__)

# load_dotenv() searches upward from the cwd and would miss data/.env (a
# subdirectory, not an ancestor) when run from the project root — point it
# at the file directly, same place the data pipeline keeps its credentials.
load_dotenv(Path(__file__).resolve().parent.parent / "data" / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.repository = Repository(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
    )
    app.state.conversations = ConversationStore(os.getenv("REDIS_URL"))
    # (city_id, user_id) -> Orchestrator, built lazily on first use against a
    # real city name pulled from the graph. Keyed per-user because each
    # orchestrator's remember_user_fact tool is bound to one user_id.
    app.state.orchestrators = {}
    yield
    app.state.repository.close()
    app.state.conversations.close()


app = FastAPI(title="Local Buddy", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateSession(BaseModel):
    city_id: str
    user_id: str


class ChatMessage(BaseModel):
    session_id: str
    message: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class RefreshRequest(BaseModel):
    city_id: str
    city_name: str
    # "all" (full pipeline), one of DataIngestionPipeline.LINK_TARGETS' keys
    # (attractions/hotels/restaurants — re-collect just that category), or
    # "verify_prices" (web-search + LLM-extract current hotel prices).
    scope: str
    # Caps how many hotels get verified in one verify_prices call — verifying an
    # entire city can take minutes (one search + one LLM call per hotel).
    limit: Optional[int] = None


def _orchestrator_for(request: Request, city_id: str, user_id: str):
    orchestrators = request.app.state.orchestrators
    key = (city_id, user_id)
    if key not in orchestrators:
        repository = request.app.state.repository
        overview = repository.get_city_overview(city_id)
        if overview is None:
            raise HTTPException(status_code=404, detail=f"Unknown city '{city_id}'")
        orchestrators[key] = build_orchestrator(
            repository, city_id, overview["name"], request.app.state.conversations, user_id,
        )
    return orchestrators[key]


@app.post("/chat/sessions")
def create_session(payload: CreateSession, request: Request):
    repository = request.app.state.repository
    if repository.get_city_overview(payload.city_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown city '{payload.city_id}'")
    session_id = request.app.state.conversations.create_session(payload.city_id, payload.user_id)
    return {"session_id": session_id}


@app.get("/chat/sessions/{session_id}/history")
def session_history(session_id: str, request: Request):
    return request.app.state.conversations.get_full_history(session_id)


@app.get("/map/markers")
def map_markers(city_id: str, request: Request):
    repository = request.app.state.repository
    if repository.get_city_overview(city_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown city '{city_id}'")
    return repository.get_map_markers(city_id)


@app.post("/admin/refresh")
def admin_refresh(payload: RefreshRequest, request: Request):
    """Trigger a data refresh for one city. Runs synchronously — "all" or
    "verify_prices" over many hotels can take several minutes, so callers should
    use a generous client timeout (or a small `limit` for verify_prices)."""
    pipeline = DataIngestionPipeline()
    try:
        if payload.scope == "all":
            pipeline.run_full_pipeline(payload.city_name, payload.city_id)
            result = {}
        elif payload.scope in DataIngestionPipeline.LINK_TARGETS:
            count = pipeline._collect_and_load(payload.city_name, payload.city_id, payload.scope)
            label, relationship = DataIngestionPipeline.LINK_TARGETS[payload.scope]
            pipeline.neo4j_loader.link_to_nearest_area(payload.city_id, label, relationship)
            result = {"collected": count}
        elif payload.scope == "verify_prices":
            verified = pipeline.verify_hotel_prices(
                request.app.state.repository, payload.city_id, payload.city_name, limit=payload.limit,
            )
            result = {"verified": verified}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown scope '{payload.scope}'")
    finally:
        pipeline.close()
    return {"status": "done", "scope": payload.scope, **result}


@app.post("/chat/message")
def chat_message(payload: ChatMessage, request: Request):
    request_start = time.perf_counter()
    conversations = request.app.state.conversations

    redis_start = time.perf_counter()
    city_id = conversations.get_city(payload.session_id)
    user_id = conversations.get_user(payload.session_id)
    if city_id is None or user_id is None:
        raise HTTPException(status_code=404, detail=f"Unknown or expired session '{payload.session_id}'")

    orchestrator = _orchestrator_for(request, city_id, user_id)
    orchestrator.location["lat"] = payload.lat
    orchestrator.location["lng"] = payload.lng

    facts = conversations.get_user_memory(user_id)
    memory_note = (
        [{"role": "system", "content": "Known facts about this traveler: " + "; ".join(facts)}]
        if facts else []
    )
    history = conversations.get_context_window(payload.session_id)
    logger.info(f"[api] Redis read (city/user/memory/history): {time.perf_counter() - redis_start:.3f}s")

    orchestrator_start = time.perf_counter()
    reply = orchestrator.respond_to([*memory_note, *history, {"role": "user", "content": payload.message}])
    logger.info(f"[api] orchestrator.respond_to total: {time.perf_counter() - orchestrator_start:.2f}s")

    redis_write_start = time.perf_counter()
    conversations.append_message(payload.session_id, "user", payload.message)
    conversations.append_message(payload.session_id, "assistant", reply)
    logger.info(f"[api] Redis write (2 messages): {time.perf_counter() - redis_write_start:.3f}s")

    logger.info(f"[api] /chat/message TOTAL: {time.perf_counter() - request_start:.2f}s")
    return {"reply": reply}

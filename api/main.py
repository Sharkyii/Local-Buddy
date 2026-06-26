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
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agents.orchestrator import build_orchestrator
from data.conversation_store import ConversationStore
from data.ingestion_pipeline import DataIngestionPipeline
from data.repository import Repository

logger = logging.getLogger(__name__)

# load_dotenv() searches upward from the cwd and would miss data/.env (a
# subdirectory, not an ancestor) when run from the project root — point it
# at the file directly, same place the data pipeline keeps its credentials.
load_dotenv(Path(__file__).resolve().parent.parent / "data" / ".env")

# /admin/refresh can trigger expensive OSM scraping + LLM price-extraction —
# gate it behind a key so it's not wide open to the internet. If you haven't
# set ADMIN_API_KEY in data/.env, one is generated and logged once at startup
# so local dev still works without extra setup — but for anything beyond your
# own machine, set ADMIN_API_KEY explicitly instead of relying on this.
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
if not ADMIN_API_KEY:
    ADMIN_API_KEY = secrets.token_urlsafe(24)
    logger.warning(f"[admin] No ADMIN_API_KEY set — generated one for this run: {ADMIN_API_KEY}")
    logger.warning("[admin] Set ADMIN_API_KEY in data/.env to keep it stable across restarts.")


def require_admin_key(x_admin_key: str = Header(default=None)):
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-Admin-Key header")


limiter = Limiter(key_func=get_remote_address)

# Cities with a real OSM collection pipeline already run at least once.
# Bangalore is deliberately excluded — it's bootstrap-only (norms/areas, no
# OSM data), so a full pipeline run there would be a first collection, not a
# refresh; that's a separate, bigger decision than "keep existing data fresh".
SCHEDULED_REFRESH_CITIES = [
    ("ahmedabad", "Ahmedabad, India"),
    ("gwalior", "Gwalior, India"),
    ("mumbai", "Mumbai, India"),
]


def _scheduled_refresh():
    """Re-runs the full OSM pipeline for every city with existing data, daily,
    so attractions/hotels/restaurants don't go stale just because nobody
    happened to call POST /admin/refresh. Each city's failure is isolated —
    one Overpass hiccup shouldn't skip the rest."""
    logger.info("[scheduler] Starting daily data refresh...")
    pipeline = DataIngestionPipeline()
    try:
        for city_id, city_name in SCHEDULED_REFRESH_CITIES:
            try:
                pipeline.run_full_pipeline(city_name, city_id)
            except Exception as error:
                logger.error(f"[scheduler] Refresh failed for {city_id}: {error}")
    finally:
        pipeline.close()
    logger.info("[scheduler] Daily data refresh complete.")


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

    scheduler = BackgroundScheduler()
    scheduler.add_job(_scheduled_refresh, "cron", hour=3, minute=0)  # off-peak, server-local time
    scheduler.start()
    app.state.scheduler = scheduler

    yield

    scheduler.shutdown(wait=False)
    app.state.repository.close()
    app.state.conversations.close()


app = FastAPI(title="Local Buddy", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    # 5173 = web frontend (Vite). 19006 = mobile/'s Expo-web dev mode, useful
    # for testing the RN scaffold in a browser; native iOS/Android builds
    # don't go through a browser so CORS doesn't apply to them at all.
    allow_origins=["http://localhost:5173", "http://localhost:19006"],
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
@limiter.limit("10/minute")
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


@app.post("/admin/refresh", dependencies=[Depends(require_admin_key)])
@limiter.limit("5/hour")
def admin_refresh(payload: RefreshRequest, request: Request):
    """Trigger a data refresh for one city. Requires the X-Admin-Key header
    (see ADMIN_API_KEY above). Runs synchronously — "all" or "verify_prices"
    over many hotels can take several minutes, so callers should use a
    generous client timeout (or a small `limit` for verify_prices)."""
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
@limiter.limit("20/minute")
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

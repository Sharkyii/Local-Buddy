"""
Thin FastAPI chat layer — wires a traveler's message to that city's
Orchestrator, with three layers of memory (see data/conversation_store.py):
Chat History (full transcript), Session Memory (the recent-turns window fed
to the LLM), and User Memory (durable cross-session facts).

POST /chat/sessions                {"city_id", "user_id"}    -> {"session_id"}
POST /chat/message                 {"session_id", "message"} -> {"reply"}
GET  /chat/sessions/{id}/history                             -> [{"role", "content"}, ...]
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.orchestrator import build_orchestrator
from data.conversation_store import ConversationStore
from data.repository import Repository

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


@app.post("/chat/message")
def chat_message(payload: ChatMessage, request: Request):
    conversations = request.app.state.conversations
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
    reply = orchestrator.respond_to([*memory_note, *history, {"role": "user", "content": payload.message}])

    conversations.append_message(payload.session_id, "user", payload.message)
    conversations.append_message(payload.session_id, "assistant", reply)

    return {"reply": reply}

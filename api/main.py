"""
Thin FastAPI chat endpoint — wires a traveler's message to that city's
Orchestrator and returns its synthesized reply.

POST /chat/message  {"city_id": "ahmedabad", "message": "..."}  ->  {"reply": "..."}
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from agents.orchestrator import build_orchestrator
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
    # city_id -> Orchestrator, built lazily so each city's agents are wired once,
    # on first use, against a real city name pulled from the graph.
    app.state.orchestrators = {}
    yield
    app.state.repository.close()


app = FastAPI(title="Local Buddy", lifespan=lifespan)


class ChatMessage(BaseModel):
    city_id: str
    message: str


def _orchestrator_for(request: Request, city_id: str):
    orchestrators = request.app.state.orchestrators
    if city_id not in orchestrators:
        repository = request.app.state.repository
        overview = repository.get_city_overview(city_id)
        if overview is None:
            raise HTTPException(status_code=404, detail=f"Unknown city '{city_id}'")
        orchestrators[city_id] = build_orchestrator(repository, city_id, overview["name"])
    return orchestrators[city_id]


@app.post("/chat/message")
def chat_message(payload: ChatMessage, request: Request):
    orchestrator = _orchestrator_for(request, payload.city_id)
    reply = orchestrator.respond(payload.message)
    return {"city_id": payload.city_id, "reply": reply}

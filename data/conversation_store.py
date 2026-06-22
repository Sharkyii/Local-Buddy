"""
ConversationStore — Redis-backed layered chat memory.

Three layers over the same Redis instance:
  - Chat History: the full append-only transcript of a session, for UI replay.
  - Session Memory: a bounded recent-turns view over Chat History — what
    actually gets fed to the LLM as context, kept short so a long chat can't
    blow past Groq's per-minute token cap (see agents/base_agent.py).
  - User Memory: durable facts about a person (diet, budget, etc.) keyed by
    user_id, so they survive across sessions/cities — written by the
    orchestrator's remember_user_fact tool, not derived from chat history.
"""

import json
import uuid
from typing import Any, Dict, List, Optional

import redis

SESSION_TTL_SECONDS = 24 * 60 * 60  # chat history/session metadata expire after a day of inactivity
MAX_HISTORY_MESSAGES = 200  # durable transcript cap, generous — not the LLM context window
DEFAULT_CONTEXT_TURNS = 10  # Session Memory window size fed to the LLM


class ConversationStore:
    """Chat History + Session Memory + User Memory, all backed by Redis."""

    def __init__(self, redis_url: str):
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    def close(self):
        self.client.close()

    # ============ SESSIONS & CHAT HISTORY ============

    def create_session(self, city_id: str, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        key = f"session:{session_id}"
        self.client.hset(key, mapping={"city_id": city_id, "user_id": user_id})
        self.client.expire(key, SESSION_TTL_SECONDS)
        return session_id

    def get_city(self, session_id: str) -> Optional[str]:
        return self.client.hget(f"session:{session_id}", "city_id")

    def get_user(self, session_id: str) -> Optional[str]:
        return self.client.hget(f"session:{session_id}", "user_id")

    def append_message(self, session_id: str, role: str, content: str):
        messages_key = f"session:{session_id}:messages"
        self.client.rpush(messages_key, json.dumps({"role": role, "content": content}))
        self.client.ltrim(messages_key, -MAX_HISTORY_MESSAGES, -1)
        self.client.expire(messages_key, SESSION_TTL_SECONDS)
        self.client.expire(f"session:{session_id}", SESSION_TTL_SECONDS)

    def get_full_history(self, session_id: str) -> List[Dict[str, Any]]:
        """The complete durable transcript, for the UI to replay a session."""
        raw = self.client.lrange(f"session:{session_id}:messages", 0, -1)
        return [json.loads(entry) for entry in raw]

    def get_context_window(self, session_id: str, max_turns: int = DEFAULT_CONTEXT_TURNS) -> List[Dict[str, Any]]:
        """Session Memory: the most recent turns, bounded so the orchestrator's
        prompt stays well under Groq's free-tier token cap."""
        raw = self.client.lrange(f"session:{session_id}:messages", -2 * max_turns, -1)
        return [json.loads(entry) for entry in raw]

    # ============ USER MEMORY ============

    def remember_fact(self, user_id: str, fact: str):
        """Add a durable fact about this user. A set, so restating the same
        fact doesn't grow memory unboundedly. No TTL — long-term by design."""
        self.client.sadd(f"user:{user_id}:memory", fact)

    def get_user_memory(self, user_id: str) -> List[str]:
        return list(self.client.smembers(f"user:{user_id}:memory"))

"""
BaseAgent — pairs a system prompt with a fixed toolset and runs a manual
tool-use loop through LiteLLM.

LiteLLM gives every provider the same OpenAI-style `tools` / `tool_calls`
shape, so one loop here drives Claude, Groq, or a local Ollama model
depending on what's configured (see _select_model) — no per-provider
agent code needed.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import litellm

logger = logging.getLogger(__name__)

ANTHROPIC_MODEL = "anthropic/claude-opus-4-8"
GROQ_MODEL = "groq/llama-3.3-70b-versatile"
MAX_TOKENS = 2048
MAX_TOOL_ROUNDS = 8

# Groq's free tier has two transient failure modes a multi-agent chain
# routinely brushes against, both worth riding out with a retry:
#   - "tool_use_failed": Llama occasionally emits malformed pseudo-XML
#     (e.g. "<function=search_areas}>{}</function>") instead of a real tool
#     call; Groq rejects its own bad generation with a 400. It's a sampling
#     glitch, not a schema problem — re-rolling immediately almost always
#     yields a valid call.
#   - rate limits: the free tier caps at 12k tokens/minute, which an
#     orchestrator + several sub-agent rounds can exceed in one chat turn;
#     a short backoff lets the per-minute window refresh.
COMPLETION_RETRIES = 3
RATE_LIMIT_BACKOFF_SECONDS = 5

# Qwen3 is a hybrid reasoning model — it emits a long <think> trace before every
# answer unless told not to. "/no_think" is Qwen3's own documented directive for
# suppressing that trace; it's meaningless (and harmless) to every other model,
# so it's safe to always append rather than branch on which model is selected.
NO_THINK_DIRECTIVE = "\n\n/no_think"


def _select_model() -> str:
    """OLLAMA_MODEL is an explicit override — set it to force a local model even
    if ANTHROPIC_API_KEY/GROQ_API_KEY are also present (e.g. to keep everything
    on-machine, with no chance of a cloud model volunteering outside knowledge).
    Otherwise prefer Claude, then fall back to Groq's free tier."""
    if os.getenv("OLLAMA_MODEL"):
        return os.getenv("OLLAMA_MODEL")
    if os.getenv("ANTHROPIC_API_KEY"):
        return ANTHROPIC_MODEL
    if os.getenv("GROQ_API_KEY"):
        return GROQ_MODEL
    raise RuntimeError(
        "Set OLLAMA_MODEL (e.g. ollama_chat/qwen3:8b), ANTHROPIC_API_KEY, or GROQ_API_KEY "
        "to run LocalBuddy's agents."
    )


@dataclass
class Tool:
    """A function exposed to the model: its JSON-schema description plus the Python callable that runs it."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for the function's arguments
    function: Callable[..., str]

    def to_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {"name": self.name, "description": self.description, "parameters": self.parameters},
        }


class BaseAgent:
    def __init__(self, system_prompt: str, tools: List[Tool], name: str = "agent"):
        self.model = _select_model()
        self.system_prompt = system_prompt + NO_THINK_DIRECTIVE
        self.tool_schemas = [tool.to_schema() for tool in tools]
        self.tool_functions = {tool.name: tool.function for tool in tools}
        self.name = name  # identifies this agent in timing logs (e.g. "orchestrator", "travel_agent")

    def respond(self, query: str) -> str:
        """Stateless one-shot ask — used by sub-agents, which never carry memory."""
        return self._loop([
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ])

    def respond_to(self, messages: List[Dict[str, Any]]) -> str:
        """Multi-turn ask — `messages` already carries whatever the caller assembled
        (history, injected user-memory facts, the new turn); the system prompt is
        prepended here so callers never need to know it."""
        return self._loop([{"role": "system", "content": self.system_prompt}, *messages])

    def _loop(self, messages: List[Dict[str, Any]]) -> str:
        """Run the tool-use loop to completion and return the model's final text reply."""
        loop_start = time.perf_counter()
        round_num = 0
        for _ in range(MAX_TOOL_ROUNDS):
            round_num += 1
            llm_start = time.perf_counter()
            response = self._complete(messages)
            logger.info(f"[{self.name}] round {round_num} LLM call ({self.model}): "
                        f"{time.perf_counter() - llm_start:.2f}s")
            message = response.choices[0].message
            tool_calls = message.tool_calls
            if not tool_calls:
                logger.info(f"[{self.name}] total respond time: {time.perf_counter() - loop_start:.2f}s")
                return message.content or ""

            messages.append(message)
            for call in tool_calls:
                function = self.tool_functions[call.function.name]
                # Groq sometimes returns the literal string "null" for a no-arg
                # tool's arguments instead of "{}" — json.loads turns that into
                # None, and **None blows up, so coerce back to {} either way.
                arguments = json.loads(call.function.arguments or "{}") or {}
                tool_start = time.perf_counter()
                content = function(**arguments)
                logger.info(f"[{self.name}] tool '{call.function.name}': "
                            f"{time.perf_counter() - tool_start:.2f}s")
                messages.append({
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": call.function.name,
                    "content": content,
                })
        logger.info(f"[{self.name}] total respond time (max rounds hit): {time.perf_counter() - loop_start:.2f}s")

        return "I wasn't able to finish researching that — try a narrower question."

    def _complete(self, messages: List[Dict[str, Any]]):
        """Call the model, riding out Groq's transient malformed-tool-call and rate-limit hiccups."""
        for attempt in range(COMPLETION_RETRIES + 1):
            try:
                return litellm.completion(
                    model=self.model,
                    max_tokens=MAX_TOKENS,
                    messages=messages,
                    tools=self.tool_schemas,
                )
            except litellm.BadRequestError as error:
                if "tool_use_failed" not in str(error) or attempt == COMPLETION_RETRIES:
                    raise
            except litellm.RateLimitError:
                if attempt == COMPLETION_RETRIES:
                    raise
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)

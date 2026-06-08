"""
BaseAgent — pairs a system prompt with a fixed toolset and runs a manual
tool-use loop through LiteLLM.

LiteLLM gives every provider the same OpenAI-style `tools` / `tool_calls`
shape, so one loop here drives either Claude or Groq depending on which API
key is configured (see _select_model) — no per-provider agent code needed.
"""

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import litellm

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


def _select_model() -> str:
    """Prefer Claude when ANTHROPIC_API_KEY is set; fall back to Groq's free tier."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return ANTHROPIC_MODEL
    if os.getenv("GROQ_API_KEY"):
        return GROQ_MODEL
    raise RuntimeError("Set ANTHROPIC_API_KEY (preferred) or GROQ_API_KEY to run LocalBuddy's agents.")


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
    def __init__(self, system_prompt: str, tools: List[Tool]):
        self.model = _select_model()
        self.system_prompt = system_prompt
        self.tool_schemas = [tool.to_schema() for tool in tools]
        self.tool_functions = {tool.name: tool.function for tool in tools}

    def respond(self, query: str) -> str:
        """Run the tool-use loop to completion and return the model's final text reply."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ]

        for _ in range(MAX_TOOL_ROUNDS):
            response = self._complete(messages)
            message = response.choices[0].message
            tool_calls = message.tool_calls
            if not tool_calls:
                return message.content or ""

            messages.append(message)
            for call in tool_calls:
                function = self.tool_functions[call.function.name]
                arguments = json.loads(call.function.arguments or "{}")
                messages.append({
                    "tool_call_id": call.id,
                    "role": "tool",
                    "name": call.function.name,
                    "content": function(**arguments),
                })

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

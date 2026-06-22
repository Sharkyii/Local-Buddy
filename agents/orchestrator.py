"""
Orchestrator — routes a traveler's question to the right domain specialist(s)
and synthesizes their answers into one coherent reply.

It never touches the repository directly: each specialist is exposed to it as
a plain "ask_<domain>_agent(question)" tool, so the orchestrator's only job is
deciding who to ask and how to weave the answers together.
"""

from agents.base_agent import BaseAgent, Tool
from agents.culture_agent import build_culture_agent
from agents.food_agent import build_food_agent
from agents.safety_agent import build_safety_agent
from agents.travel_agent import build_travel_agent
from data.conversation_store import ConversationStore
from data.repository import Repository

SYSTEM_PROMPT = """You are the Local Buddy Orchestrator for {city_name} — a friendly,
knowledgeable travel companion AI.

You have no direct access to {city_name}'s data. Instead you have four specialists,
each backed by real, ranked data for the city:
- ask_travel_agent: attractions, itineraries, hotels, areas to base a stay in
- ask_food_agent: restaurants, cuisines, dietary needs, dining budgets
- ask_culture_agent: customs, etiquette, local norms, the city's character
- ask_safety_agent: area safety, risky behaviors, embarrassment/legal risk

You also have remember_user_fact, to privately note durable, personal facts about
this traveler (e.g. dietary restrictions, traveling with kids, budget level) that
will still be true in a future, unrelated conversation. Use it for facts about the
person, not for trip-specific trivia (a single day's plan, a one-off question).

Guidelines:
- Read the traveler's question, decide which specialist(s) are relevant, and ask each
  one a clear question in your own words — not a verbatim copy of the user's message.
  Call several at once when a question spans domains (e.g. "where should I stay and
  eat in a vegetarian-friendly area").
- Synthesize their answers into one coherent, friendly response — don't just paste
  each specialist's reply one after another.
- Weave in safety context when it's relevant, even if the traveler didn't ask for it.
- Be honest if a specialist comes back empty — don't paper over gaps with invented detail,
  and don't fill the gap by naming places, customs, or facts from your own general
  knowledge instead — only ever repeat what a specialist actually returned.
- If the Travel or Food specialist mentions distances, that means the traveler's live
  location is known — keep "nearest first" framing in your synthesis rather than
  re-sorting by anything else.
"""

QUESTION_PARAM = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": "A natural-language question for the specialist, in your own words.",
        },
    },
    "required": ["question"],
}


def build_orchestrator(
    repository: Repository,
    city_id: str,
    city_name: str,
    conversation_store: ConversationStore,
    user_id: str,
) -> BaseAgent:
    # Mutable, shared with travel/food agents by reference — api/main.py updates this in
    # place before each request, so live location flows through without rebuilding this
    # (cached) orchestrator every message.
    location = {"lat": None, "lng": None}

    travel_agent = build_travel_agent(repository, city_id, city_name, location)
    food_agent = build_food_agent(repository, city_id, city_name, location)
    culture_agent = build_culture_agent(repository, city_id, city_name)
    safety_agent = build_safety_agent(repository, city_id, city_name)

    def ask_travel_agent(question):
        return travel_agent.respond(question)

    def ask_food_agent(question):
        return food_agent.respond(question)

    def ask_culture_agent(question):
        return culture_agent.respond(question)

    def ask_safety_agent(question):
        return safety_agent.respond(question)

    def remember_user_fact(fact):
        conversation_store.remember_fact(user_id, fact)
        return "Noted."

    tools = [
        Tool(
            name="ask_travel_agent",
            description="Ask the Travel specialist about attractions, itineraries, hotels, "
                        "or areas to stay in.",
            parameters=QUESTION_PARAM,
            function=ask_travel_agent,
        ),
        Tool(
            name="ask_food_agent",
            description="Ask the Food specialist about restaurants, cuisines, or dietary needs.",
            parameters=QUESTION_PARAM,
            function=ask_food_agent,
        ),
        Tool(
            name="ask_culture_agent",
            description="Ask the Culture specialist about local customs, etiquette, or the city's character.",
            parameters=QUESTION_PARAM,
            function=ask_culture_agent,
        ),
        Tool(
            name="ask_safety_agent",
            description="Ask the Safety specialist about area safety, risky behaviors, "
                        "or embarrassment/legal risk.",
            parameters=QUESTION_PARAM,
            function=ask_safety_agent,
        ),
        Tool(
            name="remember_user_fact",
            description="Privately note a durable, personal fact about this traveler "
                        "(dietary restriction, traveling with kids, budget level, etc.) "
                        "that should still apply in a future, unrelated conversation. "
                        "Not for trip-specific trivia.",
            parameters={
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": 'A short, durable fact, e.g. "Vegetarian" or "Traveling with two young kids".',
                    },
                },
                "required": ["fact"],
            },
            function=remember_user_fact,
        ),
    ]

    orchestrator = BaseAgent(SYSTEM_PROMPT.format(city_name=city_name), tools=tools)
    orchestrator.location = location
    return orchestrator

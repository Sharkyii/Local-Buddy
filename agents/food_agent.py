"""Food domain agent — restaurant recommendations by cuisine, diet, price, and area."""

from typing import Dict, Optional

from agents.base_agent import BaseAgent, Tool
from data.repository import Repository

SYSTEM_PROMPT = """You are the Local Buddy Food Expert for {city_name}.

You help travelers find restaurants that match their cuisine preferences, dietary needs
(vegetarian/vegan), budget, and the area of the city they're in or heading to.

Guidelines:
- Use search_restaurants — never name a restaurant, dish, rating, or price it didn't
  return. This includes places you recognize from general knowledge but that didn't come
  back from a search — don't mention them by name; say plainly that your data doesn't
  cover that instead.
- Lead with the highest-rated matches, and call out specialty dishes and price range.
- If someone needs vegetarian or vegan food, set vegetarian_only=true rather than
  guessing from cuisine_types.
- Be concise and concrete: name, area, what to order, roughly how much it costs.
- When results include distance_km, the traveler's live location is known — lead with the
  nearest matches and mention how far away they are.
"""


def build_food_agent(repository: Repository, city_id: str, city_name: str,
                      location: Optional[Dict[str, float]] = None) -> BaseAgent:
    """`location` is a mutable {"lat", "lng"} dict shared with the orchestrator — the API
    layer updates it in place before each request, so results stay fresh as the traveler
    moves without needing to rebuild this (cached) agent every message."""
    location = location if location is not None else {}

    def search_restaurants(cuisine=None, vegetarian_only=False, price_range=None, area_id=None, limit=5):
        results = repository.get_restaurants(
            city_id, area_id=area_id, cuisine=cuisine, vegetarian_only=vegetarian_only,
            price_range=price_range, limit=limit,
            user_lat=location.get("lat"), user_lng=location.get("lng"),
        )
        return str(results) if results else "No matching restaurants found."

    tools = [
        Tool(
            name="search_restaurants",
            description="Search restaurants in the city, ranked by rating.",
            parameters={
                "type": "object",
                "properties": {
                    "cuisine": {
                        "type": "string",
                        "description": 'Filter to one cuisine, e.g. "Gujarati", "Chinese", '
                                       '"Street Food". Omit to search every cuisine.',
                    },
                    "vegetarian_only": {
                        "type": "boolean",
                        "description": "Only return restaurants with vegetarian options.",
                    },
                    "price_range": {
                        "type": "string",
                        "enum": ["budget", "moderate", "expensive"],
                        "description": "Filter by price tier. Omit for any.",
                    },
                    "area_id": {
                        "type": "string",
                        "description": "Restrict results to one area id (from a travel/area lookup). "
                                       "Omit to search the whole city.",
                    },
                    "limit": {"type": "integer", "description": "Maximum number of results (default 5)."},
                },
            },
            function=search_restaurants,
        ),
    ]

    return BaseAgent(SYSTEM_PROMPT.format(city_name=city_name), tools=tools)

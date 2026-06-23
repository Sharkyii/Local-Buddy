"""Food domain agent — restaurant recommendations by cuisine, diet, price, and area."""

from typing import Dict, Optional

from agents.base_agent import BaseAgent, Tool
from data.repository import Repository
from data.reranker import rerank

SYSTEM_PROMPT = """You are the Local Buddy Food Expert for {city_name}.

You help travelers find restaurants that match their cuisine preferences, dietary needs
(vegetarian/vegan), budget, and the area of the city they're in or heading to.

Guidelines:
- Use search_restaurants — never name a restaurant, dish, rating, or price it didn't
  return. This includes places you recognize from general knowledge but that didn't come
  back from a search — don't mention them by name; say plainly that your data doesn't
  cover that instead.
- NEVER invent or guess an area_id. It must be an exact id string returned by
  search_areas (e.g. "area_satellite_ahmedabad") — call search_areas first if the
  traveler names a neighborhood. If they didn't mention a specific area, omit area_id
  entirely rather than passing a made-up value (a wrong area_id silently returns zero
  results, which you must then report honestly, not paper over with invented places).
- If search_restaurants returns "No matching restaurants found", say so plainly. Do not
  substitute restaurants of a different cuisine and imply they match what was asked for.
- Lead with the highest-rated matches, and call out specialty dishes and price range.
- If someone needs vegetarian or vegan food, set vegetarian_only=true rather than
  guessing from cuisine_types.
- Be concise and concrete: name, area, what to order, roughly how much it costs.
- Results are pre-ranked best-first (by rating, distance, and uniqueness combined) —
  present them in the order given, and use each result's match_reasons to explain WHY
  it's a good pick. Don't re-sort by a single field like rating alone.
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
        if not results:
            return "No matching restaurants found."
        rerank(results, category_field="cuisine_types")  # no strong "importance" signal for restaurants
        return str(results)

    def search_areas():
        results = repository.get_areas(city_id)
        return str(results) if results else "No area data found."

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
                        "description": "Restrict results to one area id — MUST be an exact id from "
                                       "search_areas (e.g. \"area_satellite_ahmedabad\"); call "
                                       "search_areas first to get one. Never guess or invent this "
                                       "value. Omit to search the whole city.",
                    },
                    "limit": {"type": "integer", "description": "Maximum number of results (default 5)."},
                },
            },
            function=search_restaurants,
        ),
        Tool(
            name="search_areas",
            description="List the city's areas/neighborhoods with their vibe, safety level, and "
                        "what they're notable for. Use this to find the real area id for "
                        "search_restaurants when the traveler names a specific neighborhood.",
            parameters={"type": "object", "properties": {}},
            function=search_areas,
        ),
    ]

    return BaseAgent(SYSTEM_PROMPT.format(city_name=city_name), tools=tools, name="food_agent")

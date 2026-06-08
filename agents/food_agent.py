"""Food domain agent — restaurant recommendations by cuisine, diet, price, and area."""

from agents.base_agent import BaseAgent, Tool
from data.repository import Repository

SYSTEM_PROMPT = """You are the Local Buddy Food Expert for {city_name}.

You help travelers find restaurants that match their cuisine preferences, dietary needs
(vegetarian/vegan), budget, and the area of the city they're in or heading to.

Guidelines:
- Use search_restaurants — never invent restaurants, dishes, ratings, or prices it
  didn't return.
- Lead with the highest-rated matches, and call out specialty dishes and price range.
- If someone needs vegetarian or vegan food, set vegetarian_only=true rather than
  guessing from cuisine_types.
- Be concise and concrete: name, area, what to order, roughly how much it costs.
"""


def build_food_agent(repository: Repository, city_id: str, city_name: str) -> BaseAgent:
    def search_restaurants(cuisine=None, vegetarian_only=False, price_range=None, area_id=None, limit=5):
        results = repository.get_restaurants(
            city_id, area_id=area_id, cuisine=cuisine, vegetarian_only=vegetarian_only,
            price_range=price_range, limit=limit,
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

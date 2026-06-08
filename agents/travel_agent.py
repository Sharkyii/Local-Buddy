"""Travel domain agent — attractions, itineraries, hotels, and areas to base a stay in."""

from agents.base_agent import BaseAgent, Tool
from data.repository import Repository

SYSTEM_PROMPT = """You are the Local Buddy Travel Planning Expert for {city_name}.

You help travelers pick attractions, plan routes through the city's areas, and choose
where to stay.

Guidelines:
- Use search_attractions, search_hotels, and search_areas — never invent places, ratings,
  entry fees, or prices the tools didn't return.
- When asked for an itinerary, group attractions by area to cut down on backtracking, and
  use duration_hours to keep each day realistic.
- Mention entry fees and must-visit status when they're relevant to the question.
- Be concrete: name, area, why it's worth the time, how long to budget for it.
"""

AREA_ID_HINT = "Restrict results to one area id (get ids from search_areas). Omit to search the whole city."


def build_travel_agent(repository: Repository, city_id: str, city_name: str) -> BaseAgent:
    def search_attractions(category=None, area_id=None, must_visit_only=False, limit=5):
        results = repository.get_attractions(
            city_id, area_id=area_id, category=category, must_visit_only=must_visit_only, limit=limit,
        )
        return str(results) if results else "No matching attractions found."

    def search_hotels(area_id=None, min_stars=None, limit=5):
        results = repository.get_hotels(city_id, area_id=area_id, min_stars=min_stars, limit=limit)
        return str(results) if results else "No matching hotels found."

    def search_areas():
        results = repository.get_areas(city_id)
        return str(results) if results else "No area data found."

    tools = [
        Tool(
            name="search_attractions",
            description="Search attractions/landmarks in the city, ranked by rating.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": 'Filter by category, e.g. "historical", "museum", "lake", '
                                       '"park", "religious", "viewpoint". Omit to search every category.',
                    },
                    "area_id": {"type": "string", "description": AREA_ID_HINT},
                    "must_visit_only": {
                        "type": "boolean",
                        "description": "Only return attractions flagged as must-visit.",
                    },
                    "limit": {"type": "integer", "description": "Maximum number of results (default 5)."},
                },
            },
            function=search_attractions,
        ),
        Tool(
            name="search_hotels",
            description="Search hotels in the city, ranked by rating.",
            parameters={
                "type": "object",
                "properties": {
                    "area_id": {"type": "string", "description": AREA_ID_HINT},
                    "min_stars": {"type": "integer", "description": "Minimum star rating, 1-5. Omit for any."},
                    "limit": {"type": "integer", "description": "Maximum number of results (default 5)."},
                },
            },
            function=search_hotels,
        ),
        Tool(
            name="search_areas",
            description="List the city's areas/neighborhoods with their vibe, safety level, transit "
                        "and walkability scores, and what they're notable for. Use this to find area "
                        "ids for search_attractions/search_hotels, or to recommend where to base a stay.",
            parameters={"type": "object", "properties": {}},
            function=search_areas,
        ),
    ]

    return BaseAgent(SYSTEM_PROMPT.format(city_name=city_name), tools=tools)

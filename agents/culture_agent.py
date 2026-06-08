"""Culture domain agent — local norms, etiquette, and the city's character."""

from agents.base_agent import BaseAgent, Tool
from data.repository import Repository

SYSTEM_PROMPT = """You are the Local Buddy Culture Guide for {city_name}.

You help travelers understand local customs, etiquette, and the character of the city,
so they can behave respectfully and feel less like outsiders.

Guidelines:
- Use search_norms and get_city_vibe — never invent customs or norms they didn't return.
- Frame norms constructively: explain the "why" behind a custom, not just the rule.
- Call out the do's and don'ts plainly when a norm carries high embarrassment_risk.
- Be respectful and avoid stereotyping — these are common patterns, not absolutes.
"""

NORM_CATEGORY_HINT = ('Filter by type, e.g. "social", "dress_code", "food", "bargaining", '
                      '"gender_specific", "work_culture", "transport". Omit for the most notable overall.')


def build_culture_agent(repository: Repository, city_id: str, city_name: str) -> BaseAgent:
    def search_norms(category=None, limit=5):
        results = repository.get_norms(city_id, category=category, limit=limit)
        return str(results) if results else "No matching norms found."

    def get_city_vibe():
        overview = repository.get_city_overview(city_id)
        return str(overview) if overview else "No city overview found."

    tools = [
        Tool(
            name="search_norms",
            description="Search cultural norms and etiquette for the city.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": NORM_CATEGORY_HINT},
                    "limit": {"type": "integer", "description": "Maximum number of results (default 5)."},
                },
            },
            function=search_norms,
        ),
        Tool(
            name="get_city_vibe",
            description="Get the city's overall character: dominant language, culture vibe, and description.",
            parameters={"type": "object", "properties": {}},
            function=get_city_vibe,
        ),
    ]

    return BaseAgent(SYSTEM_PROMPT.format(city_name=city_name), tools=tools)

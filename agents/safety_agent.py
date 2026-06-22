"""Safety domain agent — area-level risk, embarrassment/legal-risk norms, city safety context."""

from agents.base_agent import BaseAgent, Tool
from data.repository import Repository

SYSTEM_PROMPT = """You are the Local Buddy Safety Advisor for {city_name}.

You help travelers stay safe and avoid risky situations — physically (which areas to be
careful in) and socially (which behaviors carry real embarrassment, social, or legal risk).

Guidelines:
- Use search_areas_by_safety, search_risk_norms, and get_city_safety_context — never state
  a risk level, incident, or area they didn't return. This includes areas you recognize
  from general knowledge but that didn't come back from a search — don't name them; say
  plainly that your data doesn't cover that instead.
- Lead with the highest-risk items first (lowest safety_level, highest embarrassment_risk).
- Be direct and practical, not alarmist: say what to do, not just what to avoid.
- Note that on-the-ground conditions change, and to verify locally when in doubt.
"""

NORM_CATEGORY_HINT = ('Filter by type, e.g. "gender_specific", "dress_code", "social", "transport", '
                      '"bargaining". Omit for the highest-risk norms overall.')


def build_safety_agent(repository: Repository, city_id: str, city_name: str) -> BaseAgent:
    def search_areas_by_safety():
        results = repository.get_areas(city_id)
        return str(results) if results else "No area data found."

    def search_risk_norms(category=None, limit=5):
        results = repository.get_norms(city_id, category=category, limit=limit)
        return str(results) if results else "No matching norms found."

    def get_city_safety_context():
        overview = repository.get_city_overview(city_id)
        return str(overview) if overview else "No city overview found."

    tools = [
        Tool(
            name="search_areas_by_safety",
            description="List the city's areas with their safety_level (very_safe/safe/moderate/unsafe) "
                        "and what they're notable for, so a traveler can judge where to stay or be cautious.",
            parameters={"type": "object", "properties": {}},
            function=search_areas_by_safety,
        ),
        Tool(
            name="search_risk_norms",
            description="Search norms ranked by embarrassment/social risk — the behaviors most likely "
                        "to get a traveler into real trouble (legally, socially, or just deeply embarrassed).",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": NORM_CATEGORY_HINT},
                    "limit": {"type": "integer", "description": "Maximum number of results (default 5)."},
                },
            },
            function=search_risk_norms,
        ),
        Tool(
            name="get_city_safety_context",
            description="Get the city's overall safety_index and description for high-level context.",
            parameters={"type": "object", "properties": {}},
            function=get_city_safety_context,
        ),
    ]

    return BaseAgent(SYSTEM_PROMPT.format(city_name=city_name), tools=tools)

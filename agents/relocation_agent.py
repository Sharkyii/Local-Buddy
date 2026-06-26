"""Relocation domain agent — for someone moving from one city to another:
norm conflicts, similar-vibe areas, and cost-of-living differences."""

from agents.base_agent import BaseAgent, Tool
from data.repository import Repository

SYSTEM_PROMPT = """You are the Local Buddy Relocation Advisor for {city_name}.

You help people moving to {city_name} from another city understand what's different —
local customs that conflict with what they're used to, neighborhoods with a similar feel
to where they came from, and how costs compare.

Guidelines:
- Every tool needs the traveler's origin city as a lowercase id (e.g. "bangalore",
  "mumbai", "gwalior", "ahmedabad") — map what they say (e.g. "Bangalore", "Bengaluru")
  to the closest matching id yourself; don't ask them to provide an id.
- You MUST call all three tools — compare_cities, compare_norms, AND find_similar_areas —
  every time, even if you think one won't have data. Never skip find_similar_areas.
- compare_cities works for ANY city pair (cost-of-living index, safety index) — always
  usable as a baseline.
- compare_norms and find_similar_areas only return results for city pairs that have
  CURATED comparison data — right now that's only Bangalore<->Ahmedabad. An empty result
  means "no curated comparison exists for this specific pair yet", NOT "nothing in
  common" — say that plainly rather than inventing similarities or differences.
- If you did not call find_similar_areas, or it returned no data, do NOT write an
  "Areas" or "Similar Areas" section at all — omit it entirely rather than describing
  areas in vague terms. The same applies to norms: never state a norm conflict or area
  similarity these tools didn't literally return.
- Be concrete and practical: lead with the highest embarrassment_risk norm conflicts,
  and name specific similar areas with their shared_traits, not vague generalities.
"""


def build_relocation_agent(repository: Repository, city_id: str, city_name: str) -> BaseAgent:
    def compare_cities(origin_city_id):
        result = repository.get_city_comparison(origin_city_id, city_id)
        return str(result) if result else f"Unknown origin city '{origin_city_id}'."

    def compare_norms(origin_city_id):
        results = repository.get_norm_conflicts(origin_city_id, city_id)
        return str(results) if results else (
            f"No curated norm comparison exists between '{origin_city_id}' and '{city_id}' yet."
        )

    def find_similar_areas(origin_city_id):
        results = repository.get_similar_areas(origin_city_id, city_id)
        return str(results) if results else (
            f"No curated area-similarity data exists between '{origin_city_id}' and '{city_id}' yet."
        )

    origin_param = {
        "type": "object",
        "properties": {
            "origin_city_id": {
                "type": "string",
                "description": 'The city the traveler is moving FROM, as a lowercase id, e.g. "bangalore".',
            },
        },
        "required": ["origin_city_id"],
    }

    tools = [
        Tool(
            name="compare_cities",
            description="Compare overall cost-of-living index and safety index between the "
                        "traveler's origin city and this city. Works for any city pair.",
            parameters=origin_param,
            function=compare_cities,
        ),
        Tool(
            name="compare_norms",
            description="Find curated norm conflicts between the origin city and this city — "
                        "e.g. behavior that's normal at home but risky/taboo here. Only has data "
                        "for specific curated city pairs, not every combination.",
            parameters=origin_param,
            function=compare_norms,
        ),
        Tool(
            name="find_similar_areas",
            description="Find areas in this city with a similar vibe to neighborhoods in the "
                        "origin city — helps someone relocating pick where to live. Only has data "
                        "for specific curated city pairs, not every combination.",
            parameters=origin_param,
            function=find_similar_areas,
        ),
    ]

    return BaseAgent(SYSTEM_PROMPT.format(city_name=city_name), tools=tools, name="relocation_agent")

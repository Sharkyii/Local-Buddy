"""Travel domain agent — attractions, itineraries, hotels, and areas to base a stay in."""

from typing import Dict, Optional

from ddgs import DDGS

from agents.base_agent import BaseAgent, Tool
from data.repository import Repository
from data.reranker import rerank

SYSTEM_PROMPT = """You are the Local Buddy Travel Planning Expert for {city_name}.

You help travelers pick attractions, plan routes through the city's areas, choose where
to stay, plan weekend getaways (resorts, parks, nature spots), find schools/colleges/
universities for someone relocating with family, and check current prices for hotels,
resorts, or rental flats if they're considering relocating.

Guidelines:
- Use search_attractions, search_hotels, and search_areas — never name a place, rating,
  entry fee, or price the tools didn't return. This includes places you recognize from
  general knowledge but that didn't come back from a search — don't mention them by name;
  say plainly that your data doesn't cover that instead.
- When asked for an itinerary, group attractions by area to cut down on backtracking, and
  use duration_hours to keep each day realistic.
- Mention entry fees and must-visit status when they're relevant to the question.
- Be concrete: name, area, why it's worth the time, how long to budget for it.
- Results from search_attractions/search_hotels are pre-ranked best-first (by rating,
  distance, importance, and uniqueness combined) — present them in the order given, and
  use each result's match_reasons to explain WHY it's a good pick instead of just listing
  raw stats. Don't re-sort by a single field like rating alone.
- When results include distance_km, the traveler's live location is known — lead with the
  nearest matches and mention how far away they are.
- For general cost-of-living questions (typical rent, meals, transport, groceries — by
  neighborhood where available), use get_cost_of_living first — it's real curated data,
  more trustworthy than a live search. Only fall back to check_live_price for a SPECIFIC
  named hotel/flat's current price, which get_cost_of_living won't have. Always tell the
  traveler check_live_price figures are live web results, not verified bookings, and to
  confirm before paying anything.
- search_hotels' "resort" type rarely returns anything for Indian cities — OpenStreetMap
  almost never tags real resorts that way, even at hill stations/getaway towns, so an
  empty result there does NOT mean none exist. For weekend-getaway/resort questions,
  if search_hotels comes back empty, immediately try check_live_price (e.g. "best resorts
  near {city_name} for a weekend trip") instead of just reporting no results.
"""

AREA_ID_HINT = ("Restrict results to one area id — MUST be an exact id from search_areas "
                "(e.g. \"area_satellite_ahmedabad\"); call search_areas first to get one. "
                "Never guess or invent this value. Omit to search the whole city.")


def build_travel_agent(repository: Repository, city_id: str, city_name: str,
                        location: Optional[Dict[str, float]] = None) -> BaseAgent:
    """`location` is a mutable {"lat", "lng"} dict shared with the orchestrator — the API
    layer updates it in place before each request, so results stay fresh as the traveler
    moves without needing to rebuild this (cached) agent every message."""
    location = location if location is not None else {}

    def search_attractions(category=None, area_id=None, must_visit_only=False, limit=5):
        results = repository.get_attractions(
            city_id, area_id=area_id, category=category, must_visit_only=must_visit_only, limit=limit,
            user_lat=location.get("lat"), user_lng=location.get("lng"),
        )
        if not results:
            return "No matching attractions found."
        rerank(results, importance_field="must_visit", category_field="category")
        return str(results)

    def search_hotels(area_id=None, min_stars=None, hotel_type=None, limit=5):
        results = repository.get_hotels(
            city_id, area_id=area_id, min_stars=min_stars, hotel_type=hotel_type, limit=limit,
            user_lat=location.get("lat"), user_lng=location.get("lng"),
        )
        if not results:
            return "No matching hotels found."
        rerank(results, importance_field="stars", category_field="hotel_type")
        return str(results)

    def search_areas():
        results = repository.get_areas(city_id)
        return str(results) if results else "No area data found."

    def get_cost_of_living(category=None):
        results = repository.get_cost_of_living(city_id, category=category)
        return str(results) if results else "No cost-of-living data found."

    def check_live_price(query):
        try:
            hits = DDGS().text(f"{query} {city_name}", max_results=4)
        except Exception as error:
            return f"Live price lookup failed ({error}). Tell the traveler to check prices themselves."
        if not hits:
            return "No live results found for that search."
        return "\n---\n".join(f"{h.get('title', '')}: {h.get('body', '')}" for h in hits)

    tools = [
        Tool(
            name="search_attractions",
            description="Search attractions, landmarks, AND practical day-to-day places "
                        "(hospitals, pharmacies, ATMs, bus/train stations, gyms) in the city, "
                        "ranked by rating.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": 'Filter by category, e.g. "historical", "museum", "lake", '
                                       '"park", "religious", "viewpoint", "shopping" (malls), '
                                       '"entertainment" (cinemas/theatres/theme parks), "nightlife" '
                                       '(clubs), "pool" (swimming pools), "healthcare" (hospitals/'
                                       'pharmacies/clinics), "finance" (ATMs/banks), "transport" '
                                       '(bus/train stations), "fitness" (gyms), "educational" (schools/'
                                       'colleges/universities), "landmark" (public art, sculptures, and '
                                       'other notable points of interest that don\'t fit a more specific '
                                       'category). Omit to search every category.',
                    },
                    "area_id": {"type": "string", "description": AREA_ID_HINT},
                    "must_visit_only": {
                        "type": "boolean",
                        "description": "Only return attractions flagged as must-visit. Most "
                                        "attractions in this dataset are NOT flagged must-visit "
                                        "(it's a small subset, not a quality filter) — leave this "
                                        "false unless the traveler specifically asked for must-see "
                                        "or top picks. Setting it for an ordinary search (e.g. "
                                        '"any X temple?") will wrongly return zero results.',
                    },
                    "limit": {"type": "integer", "description": "Maximum number of results (default 5)."},
                },
            },
            function=search_attractions,
        ),
        Tool(
            name="search_hotels",
            description="Search hotels and resorts in the city, ranked by rating (or distance if "
                        "the traveler's location is known). Note: no pricing data exists in this "
                        "dataset — for current rates, use check_live_price instead.",
            parameters={
                "type": "object",
                "properties": {
                    "area_id": {"type": "string", "description": AREA_ID_HINT},
                    "min_stars": {"type": "integer", "description": "Minimum star rating, 1-5. Omit for any."},
                    "hotel_type": {
                        "type": "string",
                        "enum": ["hotel", "resort", "hostel", "guest_house", "motel"],
                        "description": 'Filter by type — use "resort" for weekend-getaway questions. '
                                       "Omit to search every type.",
                    },
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
        Tool(
            name="get_cost_of_living",
            description="Real curated cost-of-living data for the city — typical rent, meal, "
                        "transport, and grocery costs, broken down by neighborhood where "
                        "available. Prefer this over check_live_price for general 'how much "
                        "does it cost to live here' questions.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["accommodation", "food", "transport"],
                        "description": "Filter to one category. Omit to get everything.",
                    },
                },
            },
            function=get_cost_of_living,
        ),
        Tool(
            name="check_live_price",
            description="Look up live info from the web for anything our database doesn't have "
                        "details on — hotel/resort rates, rental flat listings for someone "
                        "considering relocating, or background on a SPECIFIC named place (e.g. a "
                        "school/college/university's reputation, history, or admissions info — "
                        "search_attractions only returns name/location/category for these, not a "
                        "real description, since OpenStreetMap rarely has one). Results are live "
                        "web snippets, not verified facts — say so, and tell the traveler to "
                        "confirm prices before paying anything.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": 'A specific search query, e.g. "Hotel Sangrila price per '
                                       'night" or "budget 1BHK flat for rent in Bodakdev". The city '
                                       "name is appended automatically.",
                    },
                },
                "required": ["query"],
            },
            function=check_live_price,
        ),
    ]

    return BaseAgent(SYSTEM_PROMPT.format(city_name=city_name), tools=tools, name="travel_agent")

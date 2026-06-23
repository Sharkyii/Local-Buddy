"""
OpenStreetMap Data Collector
Fetches attractions, hotels, and restaurants using Nominatim + Overpass API.
Free — no API key required.
"""

import time
import logging
import requests
from typing import List, Dict, Any, Optional
from data.models import (
    Place, Hotel, Restaurant, Coordinates,
    PlaceCategory, TimingHours
)

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


class OpenStreetMapCollector:
    """Collects place data from OpenStreetMap (free, no API key required)"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "LocalBuddy/1.0 (localbuddy-app)"
        })

    def _geocode(self, city_name: str) -> Optional[Dict[str, float]]:
        """Resolve city name to lat/lng via Nominatim"""
        try:
            resp = self.session.get(NOMINATIM_URL, params={
                "q": city_name, "format": "json", "limit": 1
            })
            resp.raise_for_status()
            results = resp.json()
            if not results:
                logger.error(f"City not found: {city_name}")
                return None
            loc = results[0]
            return {"lat": float(loc["lat"]), "lng": float(loc["lon"])}
        except Exception as e:
            logger.error(f"Geocoding failed for {city_name}: {e}")
            return None

    def _overpass_query(self, lat: float, lng: float, node_filters: str,
                        radius: int = 50000, retries: int = 3) -> List[Dict]:
        """Run an Overpass QL query around a point, returning OSM elements.

        Overpass's public instance rate-limits bursts of requests with a 429 —
        retry with backoff instead of returning an empty result, since an empty
        result is otherwise indistinguishable from "this city truly has none"."""
        query = f"[out:json][timeout:30];\n(\n{node_filters}\n);\nout body;"
        query = query.replace("{radius}", str(radius)).replace(
            "{lat}", str(lat)).replace("{lng}", str(lng))

        backoff_seconds = [20, 60, 120]
        for attempt in range(retries):
            try:
                resp = self.session.post(OVERPASS_URL, data={"data": query})
                if resp.status_code == 429:
                    raise requests.exceptions.HTTPError("429 rate limited", response=resp)
                resp.raise_for_status()
                return resp.json().get("elements", [])
            except Exception as e:
                is_last = attempt == retries - 1
                if is_last:
                    logger.error(f"Overpass query failed after {retries} attempts: {e}")
                    return []
                wait = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
                logger.warning(f"Overpass query failed ({e}), retrying in {wait}s "
                               f"[attempt {attempt + 1}/{retries}]...")
                time.sleep(wait)
        return []

    def search_attractions(self, city_name: str, search_radius: int = 50000,
                           result_limit: int = 50) -> List[Place]:
        logger.info(f"Searching attractions in {city_name}...")
        center = self._geocode(city_name)
        if not center:
            return []
        time.sleep(1)  # Nominatim rate limit: 1 req/s

        filters = (
            '  node["tourism"~"museum|attraction|monument|artwork|viewpoint|theme_park"]'
            "(around:{radius},{lat},{lng});\n"
            '  node["historic"~"monument|memorial|castle|ruins|archaeological_site"]'
            "(around:{radius},{lat},{lng});\n"
            '  node["amenity"="place_of_worship"](around:{radius},{lat},{lng});\n'
            '  node["leisure"~"park|garden|nature_reserve|swimming_pool|water_park|amusement_arcade"]'
            "(around:{radius},{lat},{lng});\n"
            '  node["shop"="mall"](around:{radius},{lat},{lng});\n'
            '  node["amenity"~"cinema|theatre|nightclub"](around:{radius},{lat},{lng});'
        )
        elements = self._overpass_query(center["lat"], center["lng"], filters, search_radius)

        places, seen = [], set()
        for item in elements:
            if len(places) >= result_limit:
                break
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            place = self._parse_place(item, city_name)
            if place:
                places.append(place)

        logger.info(f"✓ Found {len(places)} attractions")
        return places

    def search_utilities(self, city_name: str, search_radius: int = 50000,
                         result_limit: int = 50) -> List[Place]:
        """Practical day-to-day places — healthcare, finance, transport, fitness.
        Separate from search_attractions since these aren't sightseeing, but
        stored as the same Place node type (just new PlaceCategory values)."""
        logger.info(f"Searching utilities in {city_name}...")
        center = self._geocode(city_name)
        if not center:
            return []
        time.sleep(1)

        filters = (
            '  node["amenity"~"hospital|pharmacy|clinic"](around:{radius},{lat},{lng});\n'
            '  node["amenity"~"atm|bank"](around:{radius},{lat},{lng});\n'
            '  node["amenity"~"bus_station"](around:{radius},{lat},{lng});\n'
            '  node["highway"="bus_stop"](around:{radius},{lat},{lng});\n'
            '  node["railway"~"station|halt"](around:{radius},{lat},{lng});\n'
            '  node["leisure"="fitness_centre"](around:{radius},{lat},{lng});'
        )
        elements = self._overpass_query(center["lat"], center["lng"], filters, search_radius)

        places, seen = [], set()
        for item in elements:
            if len(places) >= result_limit:
                break
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            place = self._parse_place(item, city_name)
            if place:
                places.append(place)

        logger.info(f"✓ Found {len(places)} utilities")
        return places

    def search_hotels(self, city_name: str, search_radius: int = 50000,
                      result_limit: int = 50) -> List[Hotel]:
        logger.info(f"Searching hotels in {city_name}...")
        center = self._geocode(city_name)
        if not center:
            return []
        time.sleep(1)

        filters = (
            '  node["tourism"~"hotel|hostel|guest_house|motel|resort"]'
            "(around:{radius},{lat},{lng});"
        )
        elements = self._overpass_query(center["lat"], center["lng"], filters, search_radius)

        hotels, seen = [], set()
        for item in elements:
            if len(hotels) >= result_limit:
                break
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            hotel = self._parse_hotel(item, city_name)
            if hotel:
                hotels.append(hotel)

        logger.info(f"✓ Found {len(hotels)} hotels")
        return hotels

    def search_restaurants(self, city_name: str, search_radius: int = 50000,
                           result_limit: int = 50, cuisine: Optional[str] = None) -> List[Restaurant]:
        logger.info(f"Searching restaurants in {city_name}...")
        center = self._geocode(city_name)
        if not center:
            return []
        time.sleep(1)

        cuisine_tag = f'["cuisine"="{cuisine}"]' if cuisine else ""
        filters = (
            f'  node["amenity"~"restaurant|cafe|fast_food|bar|bistro"]{cuisine_tag}'
            "(around:{radius},{lat},{lng});"
        )
        elements = self._overpass_query(center["lat"], center["lng"], filters, search_radius)

        restaurants, seen = [], set()
        for item in elements:
            if len(restaurants) >= result_limit:
                break
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            rest = self._parse_restaurant(item, city_name)
            if rest:
                restaurants.append(rest)

        logger.info(f"✓ Found {len(restaurants)} restaurants")
        return restaurants

    # ============ PARSING HELPERS ============

    def _city_slug(self, city_name: str) -> str:
        return city_name.split(",")[0].lower().replace(" ", "_")

    def _make_id(self, name: str, city_name: str, lat: float, lng: float) -> str:
        """Name-only IDs collapse distinct real locations that share a name
        (e.g. 10 different State Bank of India branches all MERGEing into one
        node) — coordinates (~11m precision) disambiguate them while staying
        stable across re-runs of the same OSM node."""
        name_slug = name.lower().replace(" ", "_")
        return f"{name_slug}_{round(lat, 4)}_{round(lng, 4)}_{self._city_slug(city_name)}"

    def _parse_place(self, item: Dict, city_name: str) -> Optional[Place]:
        try:
            tags = item.get("tags", {})
            name = tags.get("name", "")
            lat, lng = item.get("lat"), item.get("lon")
            if not all([name, lat, lng]):
                return None

            return Place(
                id=self._make_id(name, city_name, lat, lng),
                name=name,
                city=city_name,
                area="city_center",
                place_type=tags.get("tourism") or tags.get("historic") or "point_of_interest",
                category=self._infer_category(tags),
                significance="local",
                coordinates=Coordinates(lat=lat, lng=lng),
                description=tags.get("description", tags.get("addr:street", "")),
                data_source="openstreetmap",
            )
        except Exception as e:
            logger.warning(f"Error parsing place: {e}")
            return None

    def _parse_hotel(self, item: Dict, city_name: str) -> Optional[Hotel]:
        try:
            tags = item.get("tags", {})
            name = tags.get("name", "")
            lat, lng = item.get("lat"), item.get("lon")
            if not all([name, lat, lng]):
                return None

            try:
                stars = int(float(tags.get("stars", tags.get("tourism:stars", 0))))
            except (ValueError, TypeError):
                stars = 0

            return Hotel(
                id=self._make_id(name, city_name, lat, lng),
                name=name,
                city=city_name,
                area="city_center",
                coordinates=Coordinates(lat=lat, lng=lng),
                stars=stars,
                hotel_type=tags.get("tourism", "hotel"),
                data_source="openstreetmap",
            )
        except Exception as e:
            logger.warning(f"Error parsing hotel: {e}")
            return None

    def _parse_restaurant(self, item: Dict, city_name: str) -> Optional[Restaurant]:
        try:
            tags = item.get("tags", {})
            name = tags.get("name", "")
            lat, lng = item.get("lat"), item.get("lon")
            if not all([name, lat, lng]):
                return None

            raw_cuisine = tags.get("cuisine", tags.get("amenity", "restaurant"))
            cuisine_types = [c.strip() for c in raw_cuisine.split(";")]

            return Restaurant(
                id=self._make_id(name, city_name, lat, lng),
                name=name,
                city=city_name,
                area="city_center",
                coordinates=Coordinates(lat=lat, lng=lng),
                cuisine_types=cuisine_types,
                vegetarian_options=tags.get("diet:vegetarian") == "yes",
                vegan_options=tags.get("diet:vegan") == "yes",
                data_source="openstreetmap",
            )
        except Exception as e:
            logger.warning(f"Error parsing restaurant: {e}")
            return None

    def _infer_category(self, tags: Dict[str, str]) -> PlaceCategory:
        tourism = tags.get("tourism", "")
        historic = tags.get("historic", "")
        amenity = tags.get("amenity", "")
        natural = tags.get("natural", "")
        leisure = tags.get("leisure", "")
        waterway = tags.get("waterway", "")
        water = tags.get("water", "")
        shop = tags.get("shop", "")
        highway = tags.get("highway", "")
        railway = tags.get("railway", "")

        if amenity in ("hospital", "pharmacy", "clinic"):
            return PlaceCategory.HEALTHCARE
        if amenity in ("atm", "bank"):
            return PlaceCategory.FINANCE
        if amenity == "bus_station" or highway == "bus_stop" or railway in ("station", "halt"):
            return PlaceCategory.TRANSPORT
        if leisure == "fitness_centre":
            return PlaceCategory.FITNESS
        if "museum" in tourism:
            return PlaceCategory.MUSEUM
        if historic in ("monument", "memorial", "castle", "ruins", "archaeological_site"):
            return PlaceCategory.HISTORICAL
        if amenity == "place_of_worship":
            return PlaceCategory.RELIGIOUS
        if tourism == "zoo" or leisure == "nature_reserve":
            return PlaceCategory.WILDLIFE
        if natural == "beach":
            return PlaceCategory.BEACH
        if waterway == "waterfall" or natural == "waterfall":
            return PlaceCategory.WATERFALL
        if water == "reservoir" or tags.get("man_made") == "dam":
            return PlaceCategory.DAM
        if waterway == "river":
            return PlaceCategory.RIVER
        if natural == "water" or water == "lake":
            return PlaceCategory.LAKE
        if tourism == "viewpoint" or natural == "peak":
            return PlaceCategory.VIEWPOINT
        if leisure == "garden":
            return PlaceCategory.GARDEN
        if "park" in tourism or "park" in amenity or leisure == "park":
            return PlaceCategory.PARK
        if natural in ("wood", "forest"):
            return PlaceCategory.NATURE
        if tourism == "mall" or amenity == "marketplace" or shop == "mall":
            return PlaceCategory.SHOPPING
        if amenity in ("cinema", "theatre") or leisure in ("water_park", "amusement_arcade") \
                or tourism == "theme_park":
            return PlaceCategory.ENTERTAINMENT
        if amenity == "nightclub":
            return PlaceCategory.NIGHTLIFE
        if leisure == "swimming_pool":
            return PlaceCategory.POOL
        # Covers tourism=artwork/attraction (queried for explicitly in
        # search_attractions) plus anything else with no specific rule above.
        # NOT "entertainment" — that implies cinemas/theme parks, which is
        # misleading for an arbitrary unmatched OSM node.
        return PlaceCategory.LANDMARK


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    collector = OpenStreetMapCollector()

    print("\n=== TESTING AHMEDABAD ATTRACTIONS ===")
    attractions = collector.search_attractions("Ahmedabad, India", result_limit=10)

    for attr in attractions[:3]:
        print(f"\n{attr.name}")
        print(f"  Category: {attr.category.value}")
        print(f"  Location: {attr.coordinates.lat}, {attr.coordinates.lng}")

    print(f"\n✓ Total attractions collected: {len(attractions)}")

"""
Google Maps API Collector
Fetches attractions, hotels, and restaurants from Google Places API
"""

import googlemaps
import logging
from typing import List, Dict, Any, Optional
from data.models import (
    Place, Hotel, Restaurant, Coordinates,
    PlaceCategory, TimingHours
)

logger = logging.getLogger(__name__)


class GoogleMapsCollector:
    """Collects data from Google Maps/Places API"""

    def __init__(self, api_key: str):
        """Initialize with Google Maps API key"""
        self.client = googlemaps.Client(key=api_key)
        self.logger = logger

    def search_attractions(self, city_name: str, search_radius: int = 50000,
                          result_limit: int = 50) -> List[Place]:
        """
        Search for attractions/landmarks in a city

        Args:
            city_name: "Ahmedabad", "Mumbai", etc.
            search_radius: Search radius in meters (default 50km)
            result_limit: Max results to return

        Returns:
            List of Place objects
        """
        self.logger.info(f"Searching attractions in {city_name}...")

        places = []

        try:
            # Get city center
            geocode_result = self.client.geocode(city_name)
            if not geocode_result:
                self.logger.error(f"City not found: {city_name}")
                return places

            city_center = geocode_result[0]['geometry']['location']
            self.logger.info(f"City center: {city_center}")

            # Search for tourist attractions
            search_keywords = [
                "tourist attraction",
                "monument",
                "museum",
                "historical site",
                "landmark"
            ]

            for keyword in search_keywords:
                try:
                    nearby_result = self.client.places_nearby(
                        location=city_center,
                        radius=search_radius,
                        keyword=keyword,
                        type="point_of_interest"
                    )

                    for item in nearby_result.get('results', []):
                        if len(places) >= result_limit:
                            break

                        place_obj = self._parse_place(item, city_name)
                        if place_obj:
                            places.append(place_obj)

                    # Handle pagination
                    while nearby_result.get('next_page_token') and len(places) < result_limit:
                        try:
                            self.logger.info(f"Fetching next page ({len(places)} so far)...")
                            nearby_result = self.client.places_nearby(
                                page_token=nearby_result.get('next_page_token')
                            )

                            for item in nearby_result.get('results', []):
                                if len(places) >= result_limit:
                                    break
                                place_obj = self._parse_place(item, city_name)
                                if place_obj:
                                    places.append(place_obj)
                        except Exception as e:
                            self.logger.warning(f"Error on pagination: {e}")
                            break

                except Exception as e:
                    self.logger.warning(f"Error searching for '{keyword}': {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error in search_attractions: {e}")

        self.logger.info(f"✓ Found {len(places)} attractions")
        return places

    def search_hotels(self, city_name: str, search_radius: int = 50000,
                     result_limit: int = 50) -> List[Hotel]:
        """
        Search for hotels in a city

        Returns:
            List of Hotel objects
        """
        self.logger.info(f"Searching hotels in {city_name}...")

        hotels = []

        try:
            geocode_result = self.client.geocode(city_name)
            if not geocode_result:
                return hotels

            city_center = geocode_result[0]['geometry']['location']

            nearby_result = self.client.places_nearby(
                location=city_center,
                radius=search_radius,
                type="lodging"
            )

            for item in nearby_result.get('results', []):
                if len(hotels) >= result_limit:
                    break

                hotel_obj = self._parse_hotel(item, city_name)
                if hotel_obj:
                    hotels.append(hotel_obj)

        except Exception as e:
            self.logger.error(f"Error in search_hotels: {e}")

        self.logger.info(f"✓ Found {len(hotels)} hotels")
        return hotels

    def search_restaurants(self, city_name: str, search_radius: int = 50000,
                          result_limit: int = 50, cuisine: Optional[str] = None) -> List[Restaurant]:
        """
        Search for restaurants in a city

        Args:
            city_name: City to search in
            cuisine: Optional cuisine type filter

        Returns:
            List of Restaurant objects
        """
        self.logger.info(f"Searching restaurants in {city_name}...")

        restaurants = []

        try:
            geocode_result = self.client.geocode(city_name)
            if not geocode_result:
                return restaurants

            city_center = geocode_result[0]['geometry']['location']

            search_keywords = [
                "restaurant",
                "cafe",
                "fast food",
                "bar",
                "bistro"
            ]

            if cuisine:
                search_keywords.insert(0, f"{cuisine} restaurant")

            for keyword in search_keywords:
                try:
                    nearby_result = self.client.places_nearby(
                        location=city_center,
                        radius=search_radius,
                        keyword=keyword,
                        type="restaurant"
                    )

                    for item in nearby_result.get('results', []):
                        if len(restaurants) >= result_limit:
                            break

                        rest_obj = self._parse_restaurant(item, city_name)
                        if rest_obj:
                            restaurants.append(rest_obj)

                except Exception as e:
                    self.logger.warning(f"Error searching restaurants for '{keyword}': {e}")

        except Exception as e:
            self.logger.error(f"Error in search_restaurants: {e}")

        self.logger.info(f"✓ Found {len(restaurants)} restaurants")
        return restaurants

    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed information about a place"""
        try:
            result = self.client.place(place_id)
            return result.get('result', {})
        except Exception as e:
            self.logger.warning(f"Error getting place details: {e}")
            return {}

    # ============ PARSING HELPERS ============

    def _parse_place(self, item: Dict, city_name: str) -> Optional[Place]:
        """Parse Google Places API result into Place object"""
        try:
            place_id = item.get('place_id', '')
            name = item.get('name', '')
            location = item.get('geometry', {}).get('location', {})

            if not all([place_id, name, location]):
                return None

            # Try to infer category from type
            google_types = item.get('types', [])
            category = self._infer_category(google_types)

            place = Place(
                id=f"{name.lower().replace(' ', '_')}_{city_name}",
                name=name,
                city=city_name,
                area="city_center",  # Will be updated later with actual area
                place_type=google_types[0] if google_types else "point_of_interest",
                category=category,
                significance="local",
                coordinates=Coordinates(lat=location['lat'], lng=location['lng']),
                description=item.get('vicinity', ''),
                google_places_id=place_id,
                google_rating=item.get('rating', 0.0),
                google_reviews=item.get('user_ratings_total', 0),
                data_source="google_maps"
            )

            return place

        except Exception as e:
            self.logger.warning(f"Error parsing place: {e}")
            return None

    def _parse_hotel(self, item: Dict, city_name: str) -> Optional[Hotel]:
        """Parse Google Places API result into Hotel object"""
        try:
            place_id = item.get('place_id', '')
            name = item.get('name', '')
            location = item.get('geometry', {}).get('location', {})

            if not all([place_id, name, location]):
                return None

            hotel = Hotel(
                id=f"{name.lower().replace(' ', '_')}_{city_name}",
                name=name,
                city=city_name,
                area="city_center",
                coordinates=Coordinates(lat=location['lat'], lng=location['lng']),
                google_places_id=place_id,
                google_rating=item.get('rating', 0.0),
                data_source="google_maps"
            )

            return hotel

        except Exception as e:
            self.logger.warning(f"Error parsing hotel: {e}")
            return None

    def _parse_restaurant(self, item: Dict, city_name: str) -> Optional[Restaurant]:
        """Parse Google Places API result into Restaurant object"""
        try:
            place_id = item.get('place_id', '')
            name = item.get('name', '')
            location = item.get('geometry', {}).get('location', {})

            if not all([place_id, name, location]):
                return None

            restaurant = Restaurant(
                id=f"{name.lower().replace(' ', '_')}_{city_name}",
                name=name,
                city=city_name,
                area="city_center",
                coordinates=Coordinates(lat=location['lat'], lng=location['lng']),
                cuisine_types=[item.get('types', ['restaurant'])[0]],
                google_places_id=place_id,
                google_rating=item.get('rating', 0.0),
                data_source="google_maps"
            )

            return restaurant

        except Exception as e:
            self.logger.warning(f"Error parsing restaurant: {e}")
            return None

    def _infer_category(self, types: List[str]) -> PlaceCategory:
        """Infer place category from Google types"""
        category_mapping = {
            "historical": PlaceCategory.HISTORICAL,
            "museum": PlaceCategory.MUSEUM,
            "park": PlaceCategory.PARK,
            "place_of_worship": PlaceCategory.RELIGIOUS,
            "temple": PlaceCategory.RELIGIOUS,
            "mosque": PlaceCategory.RELIGIOUS,
            "church": PlaceCategory.RELIGIOUS,
            "market": PlaceCategory.MARKET,
            "shopping_mall": PlaceCategory.SHOPPING,
        }

        for google_type in types:
            for key, category in category_mapping.items():
                if key in google_type.lower():
                    return category

        return PlaceCategory.ENTERTAINMENT


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize collector
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY not set in .env")
        exit(1)

    collector = GoogleMapsCollector(api_key)

    # Test: Get attractions for Ahmedabad
    print("\n=== TESTING AHMEDABAD ATTRACTIONS ===")
    attractions = collector.search_attractions(
        "Ahmedabad, India",
        result_limit=10
    )

    for attr in attractions[:3]:
        print(f"\n{attr.name}")
        print(f"  Category: {attr.category.value}")
        print(f"  Rating: {attr.google_rating}")
        print(f"  Location: {attr.coordinates.lat}, {attr.coordinates.lng}")

    print(f"\n✓ Total attractions collected: {len(attractions)}")

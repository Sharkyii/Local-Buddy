"""
Neo4j Data Loader
Loads collected data into Neo4j knowledge graph
"""

import json
import logging
from typing import List, Dict, Any
from neo4j import GraphDatabase
from data.models import (
    City, Area, Place, Hotel, Restaurant, Norm, PlaceCategory
)

logger = logging.getLogger(__name__)

# Maps each PlaceCategory value to a PascalCase secondary node label
# (e.g. "lake" -> "Lake") so Neo4j Browser can style each category
# distinctly via its per-label legend (color/icon/caption).
CATEGORY_LABELS = {category.value: category.value.capitalize() for category in PlaceCategory}


class Neo4jLoader:
    """Loads data models into Neo4j"""

    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j URI (e.g., "neo4j://localhost:7687")
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.logger = logger

    def close(self):
        """Close database connection"""
        self.driver.close()

    def _with_point(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Neo4j rejects nested maps as property values, so 'coordinates'
        ({lat, lng}) can't be stored directly. Pull it out as separate
        lat/lng params for use with Cypher's native point() type.
        """
        coords = data.pop('coordinates')
        data['lat'] = coords['lat']
        data['lng'] = coords['lng']
        return data

    def clear_database(self):
        """DANGER: Clear entire database. Use only for testing."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            self.logger.warning("⚠️  Database cleared!")

    # ============ CITY OPERATIONS ============

    def create_city(self, city: City) -> bool:
        """Create or update City node"""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (c:City {id: $id})
                    SET c.name = $name,
                        c.state = $state,
                        c.country = $country,
                        c.population = $population,
                        c.primary_language = $primary_language,
                        c.secondary_languages = $secondary_languages,
                        c.timezone = $timezone,
                        c.currency = $currency,
                        c.climate_type = $climate_type,
                        c.urban_density = $urban_density,
                        c.culture_vibe = $culture_vibe,
                        c.cost_of_living_index = $cost_of_living_index,
                        c.safety_index = $safety_index,
                        c.infrastructure_score = $infrastructure_score,
                        c.description = $description,
                        c.created_at = datetime()
                """, city.to_dict())
                self.logger.info(f"✓ City created: {city.name}")
                return True
        except Exception as e:
            self.logger.error(f"Error creating city: {e}")
            return False

    # ============ AREA OPERATIONS ============

    def create_area(self, area: Area) -> bool:
        """Create or update Area node and link to city"""
        try:
            with self.driver.session() as session:
                # Create Area node
                area_data = self._with_point(area.to_dict())
                session.run("""
                    MERGE (a:Area {id: $id})
                    SET a.name = $name,
                        a.city = $city,
                        a.locality_type = $locality_type,
                        a.coordinates = point({latitude: $lat, longitude: $lng}),
                        a.population = $population,
                        a.average_rent_1bhk = $average_rent_1bhk,
                        a.safety_level = $safety_level,
                        a.public_transport_score = $public_transport_score,
                        a.walkability_score = $walkability_score,
                        a.cultural_vibe = $cultural_vibe,
                        a.area_reputation = $area_reputation,
                        a.lifestyle_tags = $lifestyle_tags,
                        a.notable_for = $notable_for
                """, area_data)

                # Create HAS_AREA relationship
                session.run("""
                    MATCH (c:City {id: $city_id})
                    MATCH (a:Area {id: $area_id})
                    MERGE (c)-[:HAS_AREA]->(a)
                """, {"city_id": area.city, "area_id": area.id})

                self.logger.info(f"✓ Area created: {area.name}")
                return True

        except Exception as e:
            self.logger.error(f"Error creating area: {e}")
            return False

    # ============ PLACE OPERATIONS ============

    def create_place(self, place: Place) -> bool:
        """Create or update Place node (area linkage handled by link_to_nearest_area)"""
        try:
            with self.driver.session() as session:
                # Create Place node
                place_data = self._with_point(place.to_dict())
                place_data['entry_fee'] = json.dumps(place_data['entry_fee'])
                session.run("""
                    MERGE (p:Place {id: $id})
                    SET p.name = $name,
                        p.city = $city,
                        p.area = $area,
                        p.place_type = $place_type,
                        p.category = $category,
                        p.significance = $significance,
                        p.coordinates = point({latitude: $lat, longitude: $lng}),
                        p.description = $description,
                        p.history = $history,
                        p.duration_hours = $duration_hours,
                        p.entry_fee = $entry_fee,
                        p.google_places_id = $google_places_id,
                        p.google_rating = $google_rating,
                        p.google_reviews = $google_reviews,
                        p.must_visit = $must_visit,
                        p.distance_from_center_km = $distance_from_center_km,
                        p.created_at = datetime()
                """, place_data)

                # Stamp a secondary label matching the category (e.g. :Lake, :Museum)
                # so Neo4j Browser's per-label style panel can color/icon each
                # PlaceCategory distinctly — Cypher can't parameterize label names,
                # but PlaceCategory is a closed enum so the lookup is exhaustive.
                category_label = CATEGORY_LABELS.get(place.category.value)
                if category_label:
                    session.run(f"MATCH (p:Place {{id: $id}}) SET p:{category_label}", {"id": place.id})

                self.logger.info(f"✓ Place created: {place.name}")
                return True

        except Exception as e:
            self.logger.error(f"Error creating place: {e}")
            return False

    # ============ RESTAURANT OPERATIONS ============

    def create_restaurant(self, restaurant: Restaurant) -> bool:
        """Create or update Restaurant node"""
        try:
            with self.driver.session() as session:
                rest_data = self._with_point(restaurant.to_dict())
                session.run("""
                    MERGE (r:Restaurant {id: $id})
                    SET r.name = $name,
                        r.city = $city,
                        r.area = $area,
                        r.coordinates = point({latitude: $lat, longitude: $lng}),
                        r.cuisine_types = $cuisine_types,
                        r.specialty_dishes = $specialty_dishes,
                        r.price_range = $price_range,
                        r.average_cost_per_person = $average_cost_per_person,
                        r.vegetarian_options = $vegetarian_options,
                        r.vegan_options = $vegan_options,
                        r.google_rating = $google_rating,
                        r.ambiance = $ambiance,
                        r.created_at = datetime()
                """, rest_data)

                self.logger.info(f"✓ Restaurant created: {restaurant.name}")
                return True

        except Exception as e:
            self.logger.error(f"Error creating restaurant: {e}")
            return False

    # ============ HOTEL OPERATIONS ============

    def create_hotel(self, hotel: Hotel) -> bool:
        """Create or update Hotel node"""
        try:
            with self.driver.session() as session:
                hotel_data = self._with_point(hotel.to_dict())
                hotel_data['price_per_night'] = json.dumps(hotel_data['price_per_night'])
                session.run("""
                    MERGE (h:Hotel {id: $id})
                    SET h.name = $name,
                        h.city = $city,
                        h.area = $area,
                        h.coordinates = point({latitude: $lat, longitude: $lng}),
                        h.stars = $stars,
                        h.price_per_night = $price_per_night,
                        h.amenities = $amenities,
                        h.specialties = $specialties,
                        h.google_rating = $google_rating,
                        h.created_at = datetime()
                """, hotel_data)

                self.logger.info(f"✓ Hotel created: {hotel.name}")
                return True

        except Exception as e:
            self.logger.error(f"Error creating hotel: {e}")
            return False

    # ============ NORM OPERATIONS ============

    def create_norm(self, norm: Norm) -> bool:
        """Create or update Norm node"""
        try:
            with self.driver.session() as session:
                norm_data = norm.to_dict()
                session.run("""
                    MERGE (n:Norm {id: $id})
                    SET n.city = $city,
                        n.title = $title,
                        n.category = $category,
                        n.description = $description,
                        n.dos = $dos,
                        n.donts = $donts,
                        n.embarrassment_risk = $embarrassment_risk,
                        n.prevalence = $prevalence,
                        n.acceptability = $acceptability,
                        n.relevance_for_travelers = $relevance_for_travelers,
                        n.confidence_score = $confidence_score,
                        n.created_at = datetime()
                """, norm_data)

                # Link to city
                session.run("""
                    MATCH (c:City {id: $city_id})
                    MATCH (n:Norm {id: $norm_id})
                    MERGE (n)-[:NORMAL_IN]->(c)
                """, {"city_id": norm.city, "norm_id": norm.id})

                self.logger.info(f"✓ Norm created: {norm.title}")
                return True

        except Exception as e:
            self.logger.error(f"Error creating norm: {e}")
            return False

    # ============ AREA LINKING ============

    def link_to_nearest_area(self, city_id: str, label: str, relationship: str) -> int:
        """
        Link every node of the given label (Place/Hotel/Restaurant) in a city
        to its geographically nearest Area, using Neo4j's native point distance,
        and stamp the node's `area` property with that area's id.

        Args:
            city_id: City to scope the search to
            label: Node label to link, e.g. "Place", "Hotel", "Restaurant"
            relationship: Relationship type to create from Area to the node,
                          e.g. "HAS_PLACE", "HAS_HOTEL", "HAS_RESTAURANT"
        """
        try:
            with self.driver.session() as session:
                result = session.run(f"""
                    MATCH (c:City {{id: $city_id}})-[:HAS_AREA]->(a:Area)
                    MATCH (n:{label} {{city: c.name}})
                    WITH n, a, point.distance(n.coordinates, a.coordinates) AS dist
                    ORDER BY dist ASC
                    WITH n, head(collect(a)) AS nearest_area
                    MERGE (nearest_area)-[:{relationship}]->(n)
                    SET n.area = nearest_area.id
                    RETURN count(n) AS linked
                """, {"city_id": city_id})

                count = result.single()["linked"]
                self.logger.info(f"✓ Linked {count} {label} node(s) to nearest area")
                return count

        except Exception as e:
            self.logger.error(f"Error linking {label} nodes to areas: {e}")
            return 0

    # ============ CONFLICT EDGES ============

    def create_conflict_edge(self, norm1_id: str, norm2_id: str,
                           conflict_type: str = "taboo_in_dest",
                           confidence: float = 0.85,
                           embarrassment_risk: int = 7) -> bool:
        """
        Create CONFLICTS_WITH edge between two norms

        Args:
            norm1_id: First norm ID (origin city)
            norm2_id: Second norm ID (destination city)
            conflict_type: Type of conflict
            confidence: Confidence score (0-1)
            embarrassment_risk: Risk level (1-10)
        """
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (n1:Norm {id: $norm1_id})
                    MATCH (n2:Norm {id: $norm2_id})
                    MERGE (n1)-[c:CONFLICTS_WITH]->(n2)
                    SET c.conflict_type = $conflict_type,
                        c.confidence = $confidence,
                        c.embarrassment_risk = $embarrassment_risk,
                        c.created_at = datetime()
                """, {
                    "norm1_id": norm1_id,
                    "norm2_id": norm2_id,
                    "conflict_type": conflict_type,
                    "confidence": confidence,
                    "embarrassment_risk": embarrassment_risk
                })

                self.logger.info(f"✓ Conflict edge created: {norm1_id} -> {norm2_id}")
                return True

        except Exception as e:
            self.logger.error(f"Error creating conflict edge: {e}")
            return False

    # ============ SIMILARITY EDGES ============

    def create_similarity_edge(self, area1_id: str, area2_id: str,
                              similarity_score: float, shared_traits: List[str] = None) -> bool:
        """
        Create SIMILAR_VIBE_TO edge between two areas

        Args:
            area1_id: First area ID
            area2_id: Second area ID
            similarity_score: Score 0-1
            shared_traits: List of shared characteristics
        """
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (a1:Area {id: $area1_id})
                    MATCH (a2:Area {id: $area2_id})
                    MERGE (a1)-[s:SIMILAR_VIBE_TO]->(a2)
                    SET s.similarity_score = $similarity_score,
                        s.shared_traits = $shared_traits,
                        s.created_at = datetime()
                """, {
                    "area1_id": area1_id,
                    "area2_id": area2_id,
                    "similarity_score": similarity_score,
                    "shared_traits": shared_traits or []
                })

                self.logger.info(f"✓ Similarity edge created: {area1_id} ≈ {area2_id}")
                return True

        except Exception as e:
            self.logger.error(f"Error creating similarity edge: {e}")
            return False

    # ============ NORM CONTEXT EDGES ============

    def create_requires_context_edge(self, norm_id: str, place_id: str,
                                      relevance: str = "high", note: str = "") -> bool:
        """
        Create REQUIRES_CONTEXT edge from a Norm to a Place — flags a real-world
        location where the norm is actually observable, so the agent can ground
        an abstract cultural rule in something concrete to see/visit.

        Args:
            norm_id: Norm node id
            place_id: Place node id where the norm applies/is visible
            relevance: How central this place is to understanding the norm
                       ("high", "medium", "low")
            note: Short explanation of why this place illustrates the norm
        """
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (n:Norm {id: $norm_id})
                    MATCH (p:Place {id: $place_id})
                    MERGE (n)-[r:REQUIRES_CONTEXT]->(p)
                    SET r.relevance = $relevance,
                        r.note = $note,
                        r.created_at = datetime()
                """, {
                    "norm_id": norm_id,
                    "place_id": place_id,
                    "relevance": relevance,
                    "note": note
                })

                self.logger.info(f"✓ Context edge created: {norm_id} -> {place_id}")
                return True

        except Exception as e:
            self.logger.error(f"Error creating context edge: {e}")
            return False

    # ============ QUERY OPERATIONS ============

    def get_city_stats(self, city_id: str) -> Dict[str, Any]:
        """Get statistics about a city in the graph"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:City {id: $city_id})
                    OPTIONAL MATCH (c)-[:HAS_AREA]->(a:Area)
                    OPTIONAL MATCH (p:Place {city: c.name})
                    OPTIONAL MATCH (r:Restaurant {city: c.name})
                    OPTIONAL MATCH (h:Hotel {city: c.name})
                    OPTIONAL MATCH (n:Norm)-[:NORMAL_IN]->(c)
                    RETURN
                        c.name as city_name,
                        count(DISTINCT a) as areas,
                        count(DISTINCT p) as attractions,
                        count(DISTINCT r) as restaurants,
                        count(DISTINCT h) as hotels,
                        count(DISTINCT n) as norms
                """, {"city_id": city_id})

                record = result.single()
                if record:
                    return dict(record)
                return {}

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {}

    def get_conflicts(self, origin_city: str, dest_city: str, limit: int = 10) -> List[Dict]:
        """Get conflicting norms between two cities"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (origin_norm:Norm)-[:NORMAL_IN]->(origin:City {id: $origin_city})
                    MATCH (origin_norm)-[:CONFLICTS_WITH]->(dest_norm:Norm)
                                        -[:NORMAL_IN]->(dest:City {id: $dest_city})
                    RETURN
                        origin_norm.title as origin_norm,
                        dest_norm.title as dest_norm,
                        dest_norm.embarrassment_risk as risk,
                        dest_norm.confidence_score as confidence
                    ORDER BY risk DESC
                    LIMIT $limit
                """, {"origin_city": origin_city, "dest_city": dest_city, "limit": limit})

                return [dict(record) for record in result]

        except Exception as e:
            self.logger.error(f"Error getting conflicts: {e}")
            return []


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize loader
    loader = Neo4jLoader(
        uri=os.getenv('NEO4J_URI'),
        user=os.getenv('NEO4J_USER'),
        password=os.getenv('NEO4J_PASSWORD')
    )

    try:
        # Test: Create a city
        ahmedabad = City(
            id="ahmedabad",
            name="Ahmedabad",
            state="Gujarat",
            population=8600000,
            primary_language="Gujarati",
            safety_index=7.5,
            description="The largest city in Gujarat, known for textile industry and Gandhi heritage"
        )

        loader.create_city(ahmedabad)

        # Get stats
        stats = loader.get_city_stats("ahmedabad")
        print("\n=== CITY STATS ===")
        print(stats)

    finally:
        loader.close()

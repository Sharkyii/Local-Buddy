"""
Repository — read-only Cypher query layer over the LocalBuddy graph.

Translates concrete agent needs ("vegetarian restaurants near area X, ranked by
rating") into Cypher against Neo4j, so agents never write Cypher themselves —
they call a typed method and get back ranked, ready-to-use rows.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class Repository:
    """Concrete, ranked lookups over City/Area/Place/Restaurant/Hotel/Norm nodes."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def _query(self, cypher: str, **params) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            return [dict(record) for record in session.run(cypher, params)]

    # ============ CITY & AREAS ============

    def get_city_overview(self, city_id: str) -> Optional[Dict[str, Any]]:
        """City-level facts: language, vibe, safety index, cost of living, description."""
        rows = self._query("""
            MATCH (c:City {id: $city_id})
            RETURN c.name AS name, c.state AS state, c.country AS country,
                   c.primary_language AS primary_language, c.culture_vibe AS culture_vibe,
                   c.safety_index AS safety_index, c.cost_of_living_index AS cost_of_living_index,
                   c.description AS description
        """, city_id=city_id)
        return rows[0] if rows else None

    def get_areas(self, city_id: str) -> List[Dict[str, Any]]:
        """All areas/neighborhoods in the city with vibe, safety, and notable features."""
        return self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)
            RETURN a.id AS id, a.name AS name, a.locality_type AS locality_type,
                   a.safety_level AS safety_level, a.cultural_vibe AS vibe,
                   a.lifestyle_tags AS lifestyle_tags, a.notable_for AS notable_for,
                   a.walkability_score AS walkability_score,
                   a.public_transport_score AS public_transport_score
            ORDER BY a.name
        """, city_id=city_id)

    # ============ RESTAURANTS ============

    def get_restaurants(self, city_id: str, area_id: Optional[str] = None,
                        cuisine: Optional[str] = None, vegetarian_only: bool = False,
                        price_range: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Restaurants ranked by google_rating, optionally filtered by area/cuisine/diet/price."""
        return self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_RESTAURANT]->(r:Restaurant)
            WHERE ($area_id IS NULL OR a.id = $area_id)
              AND (NOT $vegetarian_only OR r.vegetarian_options = true)
              AND ($cuisine IS NULL OR $cuisine IN r.cuisine_types)
              AND ($price_range IS NULL OR r.price_range = $price_range)
            RETURN r.name AS name, a.name AS area, r.cuisine_types AS cuisine_types,
                   r.specialty_dishes AS specialty_dishes, r.price_range AS price_range,
                   r.average_cost_per_person AS average_cost_per_person,
                   r.vegetarian_options AS vegetarian_options, r.vegan_options AS vegan_options,
                   r.ambiance AS ambiance, r.google_rating AS rating
            ORDER BY r.google_rating DESC
            LIMIT $limit
        """, city_id=city_id, area_id=area_id, cuisine=cuisine, vegetarian_only=vegetarian_only,
             price_range=price_range, limit=limit)

    # ============ ATTRACTIONS (PLACES) ============

    def get_attractions(self, city_id: str, area_id: Optional[str] = None,
                        category: Optional[str] = None, must_visit_only: bool = False,
                        limit: int = 10) -> List[Dict[str, Any]]:
        """Attractions ranked by google_rating, optionally filtered by area/category/must-visit."""
        rows = self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_PLACE]->(p:Place)
            WHERE ($area_id IS NULL OR a.id = $area_id)
              AND ($category IS NULL OR p.category = $category)
              AND (NOT $must_visit_only OR p.must_visit = true)
            RETURN p.name AS name, a.name AS area, p.place_type AS place_type,
                   p.category AS category, p.significance AS significance,
                   p.description AS description, p.duration_hours AS duration_hours,
                   p.entry_fee AS entry_fee, p.must_visit AS must_visit,
                   p.google_rating AS rating
            ORDER BY p.google_rating DESC
            LIMIT $limit
        """, city_id=city_id, area_id=area_id, category=category,
             must_visit_only=must_visit_only, limit=limit)
        for row in rows:
            row["entry_fee"] = json.loads(row["entry_fee"]) if row["entry_fee"] else {}
        return rows

    # ============ HOTELS ============

    def get_hotels(self, city_id: str, area_id: Optional[str] = None,
                   min_stars: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Hotels ranked by google_rating, optionally filtered by area/star rating."""
        rows = self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_HOTEL]->(h:Hotel)
            WHERE ($area_id IS NULL OR a.id = $area_id)
              AND ($min_stars IS NULL OR h.stars >= $min_stars)
            RETURN h.name AS name, a.name AS area, h.stars AS stars,
                   h.price_per_night AS price_per_night, h.amenities AS amenities,
                   h.specialties AS specialties, h.google_rating AS rating
            ORDER BY h.google_rating DESC
            LIMIT $limit
        """, city_id=city_id, area_id=area_id, min_stars=min_stars, limit=limit)
        for row in rows:
            row["price_per_night"] = json.loads(row["price_per_night"]) if row["price_per_night"] else {}
        return rows

    # ============ NORMS ============

    def get_norms(self, city_id: str, category: Optional[str] = None,
                  limit: int = 10) -> List[Dict[str, Any]]:
        """Cultural norms ranked by embarrassment_risk (highest first), optionally by category."""
        return self._query("""
            MATCH (n:Norm)-[:NORMAL_IN]->(c:City {id: $city_id})
            WHERE ($category IS NULL OR n.category = $category)
            RETURN n.title AS title, n.category AS category, n.description AS description,
                   n.dos AS dos, n.donts AS donts, n.embarrassment_risk AS embarrassment_risk,
                   n.relevance_for_travelers AS relevance_for_travelers
            ORDER BY n.embarrassment_risk DESC
            LIMIT $limit
        """, city_id=city_id, category=category, limit=limit)

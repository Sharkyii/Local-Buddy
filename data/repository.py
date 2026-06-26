"""
Repository — read-only Cypher query layer over the LocalBuddy graph.

Translates concrete agent needs ("vegetarian restaurants near area X, ranked by
rating") into Cypher against Neo4j, so agents never write Cypher themselves —
they call a typed method and get back ranked, ready-to-use rows.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from data.models import category_group

logger = logging.getLogger(__name__)


class Repository:
    """Concrete, ranked lookups over City/Area/Place/Restaurant/Hotel/Norm nodes."""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def _query(self, cypher: str, **params) -> List[Dict[str, Any]]:
        start = time.perf_counter()
        with self.driver.session() as session:
            rows = [dict(record) for record in session.run(cypher, params)]
        logger.info(f"Cypher query ({len(rows)} rows): {time.perf_counter() - start:.3f}s")
        return rows

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
                        price_range: Optional[str] = None, limit: int = 10,
                        user_lat: Optional[float] = None, user_lng: Optional[float] = None) -> List[Dict[str, Any]]:
        """Restaurants ranked by distance when user_lat/user_lng are given (nearest first,
        rating as tiebreaker), else by google_rating. Optionally filtered by area/cuisine/diet/price."""
        return self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_RESTAURANT]->(r:Restaurant)
            WHERE ($area_id IS NULL OR a.id = $area_id)
              AND (NOT $vegetarian_only OR r.vegetarian_options = true)
              AND ($cuisine IS NULL OR $cuisine IN r.cuisine_types)
              AND ($price_range IS NULL OR r.price_range = $price_range)
            WITH r, a,
                 CASE WHEN $user_lat IS NOT NULL AND $user_lng IS NOT NULL
                      THEN point.distance(r.coordinates, point({latitude: $user_lat, longitude: $user_lng})) / 1000.0
                      ELSE NULL END AS distance_km
            RETURN r.name AS name, a.name AS area, r.cuisine_types AS cuisine_types,
                   r.specialty_dishes AS specialty_dishes, r.price_range AS price_range,
                   r.average_cost_per_person AS average_cost_per_person,
                   r.vegetarian_options AS vegetarian_options, r.vegan_options AS vegan_options,
                   r.ambiance AS ambiance, r.google_rating AS rating, distance_km
            ORDER BY distance_km ASC, r.google_rating DESC
            LIMIT $limit
        """, city_id=city_id, area_id=area_id, cuisine=cuisine, vegetarian_only=vegetarian_only,
             price_range=price_range, limit=limit, user_lat=user_lat, user_lng=user_lng)

    # ============ ATTRACTIONS (PLACES) ============

    def get_attractions(self, city_id: str, area_id: Optional[str] = None,
                        category: Optional[str] = None, must_visit_only: bool = False,
                        limit: int = 10, user_lat: Optional[float] = None,
                        user_lng: Optional[float] = None) -> List[Dict[str, Any]]:
        """Attractions ranked by distance when user_lat/user_lng are given (nearest first,
        rating as tiebreaker), else by google_rating. Optionally filtered by area/category/must-visit."""
        rows = self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_PLACE]->(p:Place)
            WHERE ($area_id IS NULL OR a.id = $area_id)
              AND ($category IS NULL OR p.category = $category)
              AND (NOT $must_visit_only OR p.must_visit = true)
            WITH p, a,
                 CASE WHEN $user_lat IS NOT NULL AND $user_lng IS NOT NULL
                      THEN point.distance(p.coordinates, point({latitude: $user_lat, longitude: $user_lng})) / 1000.0
                      ELSE NULL END AS distance_km
            RETURN p.name AS name, a.name AS area, p.place_type AS place_type,
                   p.category AS category, p.significance AS significance,
                   p.description AS description, p.duration_hours AS duration_hours,
                   p.entry_fee AS entry_fee, p.must_visit AS must_visit,
                   p.google_rating AS rating, distance_km
            ORDER BY distance_km ASC, p.google_rating DESC
            LIMIT $limit
        """, city_id=city_id, area_id=area_id, category=category,
             must_visit_only=must_visit_only, limit=limit, user_lat=user_lat, user_lng=user_lng)
        for row in rows:
            row["entry_fee"] = json.loads(row["entry_fee"]) if row["entry_fee"] else {}
            row["category_group"] = category_group(row["category"])
        return rows

    # ============ HOTELS ============

    def get_hotels(self, city_id: str, area_id: Optional[str] = None,
                   min_stars: Optional[int] = None, hotel_type: Optional[str] = None,
                   limit: int = 10, user_lat: Optional[float] = None,
                   user_lng: Optional[float] = None) -> List[Dict[str, Any]]:
        """Hotels/resorts ranked by distance when user_lat/user_lng are given (nearest first,
        rating as tiebreaker), else by google_rating. Optionally filtered by area/stars/type."""
        rows = self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_HOTEL]->(h:Hotel)
            WHERE ($area_id IS NULL OR a.id = $area_id)
              AND ($min_stars IS NULL OR h.stars >= $min_stars)
              AND ($hotel_type IS NULL OR h.hotel_type = $hotel_type)
            WITH h, a,
                 CASE WHEN $user_lat IS NOT NULL AND $user_lng IS NOT NULL
                      THEN point.distance(h.coordinates, point({latitude: $user_lat, longitude: $user_lng})) / 1000.0
                      ELSE NULL END AS distance_km
            RETURN h.name AS name, a.name AS area, h.stars AS stars, h.hotel_type AS hotel_type,
                   h.price_per_night AS price_per_night, h.amenities AS amenities,
                   h.specialties AS specialties, h.google_rating AS rating, distance_km
            ORDER BY distance_km ASC, h.google_rating DESC
            LIMIT $limit
        """, city_id=city_id, area_id=area_id, min_stars=min_stars, hotel_type=hotel_type,
             limit=limit, user_lat=user_lat, user_lng=user_lng)
        for row in rows:
            row["price_per_night"] = json.loads(row["price_per_night"]) if row["price_per_night"] else {}
        return rows

    # ============ MAP ============

    def get_map_markers(self, city_id: str) -> List[Dict[str, Any]]:
        """Every Place/Restaurant/Hotel/Area in the city with its real coordinates, for
        plotting on a map — one flat list, type-tagged, no agent/LLM involved."""
        rows = self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_PLACE]->(p:Place)
            RETURN p.name AS name, 'place' AS type, p.category AS category,
                   p.coordinates.latitude AS lat, p.coordinates.longitude AS lng
            UNION
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_RESTAURANT]->(r:Restaurant)
            RETURN r.name AS name, 'restaurant' AS type, null AS category,
                   r.coordinates.latitude AS lat, r.coordinates.longitude AS lng
            UNION
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)-[:HAS_HOTEL]->(h:Hotel)
            RETURN h.name AS name, 'hotel' AS type, h.hotel_type AS category,
                   h.coordinates.latitude AS lat, h.coordinates.longitude AS lng
            UNION
            MATCH (c:City {id: $city_id})-[:HAS_AREA]->(a:Area)
            RETURN a.name AS name, 'area' AS type, null AS category,
                   a.coordinates.latitude AS lat, a.coordinates.longitude AS lng
        """, city_id=city_id)
        # category_group only means something for 'place' rows — hotel_type/cuisine
        # aren't part of the PlaceCategory taxonomy, so leave those ungrouped.
        for row in rows:
            row["category_group"] = category_group(row["category"]) if row["type"] == "place" else None
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

    # ============ COST OF LIVING ============

    def get_cost_of_living(self, city_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Real curated rent/food/transport/groceries costs, optionally broken
        down by neighborhood. Prefer this over a live web search for cost-of-
        living questions — it's hand-curated, not noisy search snippets."""
        rows = self._query("""
            MATCH (c:City {id: $city_id})-[:HAS_COST_ITEM]->(item:CostOfLiving)
            WHERE ($category IS NULL OR item.category = $category)
            RETURN item.category AS category, item.item AS item,
                   item.price_min AS price_min, item.price_max AS price_max,
                   item.price_avg AS price_avg, item.neighborhood_breakdown AS neighborhood_breakdown,
                   item.compared_to_city AS compared_to_city, item.parity_ratio AS parity_ratio
            ORDER BY item.category
        """, city_id=city_id, category=category)
        for row in rows:
            row["neighborhood_breakdown"] = (
                json.loads(row["neighborhood_breakdown"]) if row["neighborhood_breakdown"] else {}
            )
        return rows

    # ============ RELOCATION / CROSS-CITY COMPARISON ============
    # CONFLICTS_WITH (Norm->Norm) and SIMILAR_VIBE_TO (Area->Area) are curated,
    # hand-authored edges between specific city pairs (currently only Bangalore
    # <-> Ahmedabad has any) — NOT auto-generated for every possible pair. An
    # empty result here means "no curated comparison exists yet for these two
    # cities", not "nothing in common" — callers must be honest about that
    # distinction rather than inventing a comparison.

    def get_city_comparison(self, city_a_id: str, city_b_id: str) -> Optional[Dict[str, Any]]:
        """High-level numbers that exist for every city (no curated cross-city
        edge needed) — cost-of-living and safety index, side by side."""
        rows = self._query("""
            MATCH (a:City {id: $city_a_id})
            MATCH (b:City {id: $city_b_id})
            RETURN a.name AS city_a, a.cost_of_living_index AS city_a_cost_index,
                   a.safety_index AS city_a_safety_index,
                   b.name AS city_b, b.cost_of_living_index AS city_b_cost_index,
                   b.safety_index AS city_b_safety_index
        """, city_a_id=city_a_id, city_b_id=city_b_id)
        return rows[0] if rows else None

    def get_norm_conflicts(self, city_a_id: str, city_b_id: str) -> List[Dict[str, Any]]:
        """Curated norm pairs that conflict between two specific cities — e.g.
        "alcohol is normal in city A, prohibited in city B". Edge direction in
        the data doesn't necessarily match which city the caller calls "origin",
        so this matches either way and labels each side by its actual city."""
        return self._query("""
            MATCH (n1:Norm)-[c:CONFLICTS_WITH]->(n2:Norm)
            MATCH (n1)-[:NORMAL_IN]->(city1:City)
            MATCH (n2)-[:NORMAL_IN]->(city2:City)
            WHERE (city1.id = $city_a_id AND city2.id = $city_b_id)
               OR (city1.id = $city_b_id AND city2.id = $city_a_id)
            RETURN city1.id AS norm1_city, n1.title AS norm1_title, n1.description AS norm1_description,
                   city2.id AS norm2_city, n2.title AS norm2_title, n2.description AS norm2_description,
                   c.conflict_type AS conflict_type, c.confidence AS confidence,
                   c.embarrassment_risk AS embarrassment_risk
            ORDER BY c.embarrassment_risk DESC
        """, city_a_id=city_a_id, city_b_id=city_b_id)

    def get_similar_areas(self, city_a_id: str, city_b_id: str) -> List[Dict[str, Any]]:
        """Curated area pairs with a similar vibe between two specific cities —
        e.g. "if you liked Indiranagar in Bangalore, try Naranpura here"."""
        return self._query("""
            MATCH (a1:Area)-[s:SIMILAR_VIBE_TO]->(a2:Area)
            MATCH (c1:City)-[:HAS_AREA]->(a1)
            MATCH (c2:City)-[:HAS_AREA]->(a2)
            WHERE (c1.id = $city_a_id AND c2.id = $city_b_id)
               OR (c1.id = $city_b_id AND c2.id = $city_a_id)
            RETURN c1.id AS area1_city, a1.name AS area1_name,
                   c2.id AS area2_city, a2.name AS area2_name,
                   s.similarity_score AS similarity_score, s.shared_traits AS shared_traits
            ORDER BY s.similarity_score DESC
        """, city_a_id=city_a_id, city_b_id=city_b_id)

"""
Data Ingestion Orchestrator
Main script to coordinate data collection and loading into Neo4j
"""

import os
import json
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import List
from data.models import City, Area, Place, Restaurant, Hotel, Norm, Coordinates, CostOfLiving
from data.collectors.osm_collector import OpenStreetMapCollector
from data.loaders.neo4j_loader import Neo4jLoader

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'logs/ingestion.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """Orchestrates entire data collection and ingestion process"""

    def __init__(self):
        self.osm_collector = OpenStreetMapCollector()
        self.neo4j_loader = Neo4jLoader(
            uri=os.getenv('NEO4J_URI'),
            user=os.getenv('NEO4J_USER'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        self.data_dir = Path(os.getenv('DATA_OUTPUT_DIR', 'data/collected'))
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def run_full_pipeline(self, city_name: str, city_id: str):
        """
        Run the complete pipeline for a city: collect attractions/hotels/
        restaurants from OpenStreetMap, load manually-curated norms/areas/
        seed-places fixtures, link everything to its nearest area, then
        self-heal any data gaps left by rate-limited OSM collection.

        Safe to re-run — every step MERGEs into Neo4j rather than duplicating.
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"STARTING PIPELINE FOR {city_name.upper()}")
        logger.info(f"{'='*60}\n")

        # Step 1: Create city in Neo4j
        logger.info(f"[STEP 1] Creating city node...")
        self.create_city_node(city_name, city_id)

        # Steps 2-4: Collect attractions, hotels, restaurants — paced to avoid
        # bursting Overpass's rate limiter (each one already retries internally,
        # but spacing the three out keeps us from tripping it in the first place)
        logger.info(f"[STEP 2] Collecting attractions from OpenStreetMap...")
        self._collect_and_load(city_name, city_id, "attractions")

        time.sleep(5)
        logger.info(f"[STEP 3] Collecting hotels from OpenStreetMap...")
        self._collect_and_load(city_name, city_id, "hotels")

        time.sleep(5)
        logger.info(f"[STEP 4] Collecting restaurants from OpenStreetMap...")
        self._collect_and_load(city_name, city_id, "restaurants")

        time.sleep(5)
        logger.info(f"[STEP 4b] Collecting utilities (healthcare/finance/transport/fitness)...")
        self._collect_and_load(city_name, city_id, "utilities")

        # Step 5: Load manual data (norms, areas, seed places, cost of living)
        logger.info(f"[STEP 5] Loading manual data from JSON fixtures...")
        self.load_manual_norms(city_id)
        self.load_manual_areas(city_id)
        self.load_manual_places(city_id)
        self.load_manual_norm_contexts(city_id)
        self.load_manual_cost_of_living(city_id)

        # Step 6: Link places/hotels/restaurants to their nearest area
        logger.info(f"[STEP 6] Linking places to nearest areas...")
        self.neo4j_loader.link_to_nearest_area(city_id, "Place", "HAS_PLACE")
        self.neo4j_loader.link_to_nearest_area(city_id, "Hotel", "HAS_HOTEL")
        self.neo4j_loader.link_to_nearest_area(city_id, "Restaurant", "HAS_RESTAURANT")

        # Step 7: Self-heal — re-collect any category that came back empty/sparse
        # (e.g. an Overpass rate-limit that exhausted its retries), so a single
        # run_full_pipeline call doesn't silently leave gaps to discover later
        logger.info(f"[STEP 7] Checking for data gaps...")
        self.collect_missing(city_name, city_id)

        # Step 8: Print summary
        logger.info(f"\n[SUMMARY] {city_name} pipeline complete!")
        stats = self.neo4j_loader.get_city_stats(city_id)
        if stats:
            logger.info(f"City: {stats.get('city_name')}")
            logger.info(f"  Areas: {stats.get('areas', 0)}")
            logger.info(f"  Attractions: {stats.get('attractions', 0)}")
            logger.info(f"  Hotels: {stats.get('hotels', 0)}")
            logger.info(f"  Restaurants: {stats.get('restaurants', 0)}")
            logger.info(f"  Norms: {stats.get('norms', 0)}")

    # Maps a collection kind to its collector search method and Neo4j loader method
    _COLLECTION_METHODS = {
        "attractions": ("search_attractions", "load_attractions_to_neo4j"),
        "hotels": ("search_hotels", "load_hotels_to_neo4j"),
        "restaurants": ("search_restaurants", "load_restaurants_to_neo4j"),
        # Practical places (healthcare/finance/transport/fitness) — same Place node
        # type as attractions, so it reuses that loader rather than duplicating it.
        "utilities": ("search_utilities", "load_attractions_to_neo4j"),
    }

    # Maps a collection kind to its (node label, Area relationship) for link_to_nearest_area
    LINK_TARGETS = {
        "attractions": ("Place", "HAS_PLACE"),
        "hotels": ("Hotel", "HAS_HOTEL"),
        "restaurants": ("Restaurant", "HAS_RESTAURANT"),
        "utilities": ("Place", "HAS_PLACE"),
    }

    def _collect_and_load(self, city_name: str, city_id: str, kind: str) -> int:
        """Collect one OSM category for a city, back it up to JSON, and load it
        into Neo4j. Returns the count collected so callers (run_full_pipeline,
        collect_missing) can detect gaps left by exhausted-retry rate limits."""
        search_method, load_method = self._COLLECTION_METHODS[kind]
        items = getattr(self.osm_collector, search_method)(
            city_name,
            result_limit=int(os.getenv('GOOGLE_PLACES_RESULTS_LIMIT', 50))
        )
        self.save_to_json(items, f"{city_id}_{kind}.json")
        getattr(self, load_method)(items)
        return len(items)

    def collect_missing(self, city_name: str, city_id: str, threshold: int = 5):
        """Re-collect any OSM category (attractions/hotels/restaurants) that came
        back suspiciously empty/sparse for a city — typically because an Overpass
        rate-limit (429) exhausted its retries during the main collection run.

        Checks live Neo4j counts (not the JSON backup, which may itself be stale)
        and only re-runs the categories that fall short of `threshold`, pacing
        each retry to avoid immediately re-tripping the rate limit."""
        stats = self.neo4j_loader.get_city_stats(city_id)
        if not stats:
            logger.warning(f"  ⚠️  No stats found for {city_id} — run run_full_pipeline first")
            return

        # "utilities" shares the Place label with "attractions", and
        # get_city_stats only reports one combined count for it (keyed
        # "attractions") — checking "utilities" here would always read as a
        # phantom gap (the key never exists) and re-collect every single run.
        gaps = [kind for kind in self._COLLECTION_METHODS
                if kind != "utilities" and stats.get(kind, 0) < threshold]

        if not gaps:
            logger.info(f"  ✓ No data gaps for {city_name} (all categories ≥ {threshold})")
            return

        logger.info(f"  ⚠️  {city_name} is short on {', '.join(gaps)} "
                    f"(< {threshold}) — re-collecting...")
        for i, kind in enumerate(gaps):
            if i > 0:
                time.sleep(15)
            count = self._collect_and_load(city_name, city_id, kind)
            logger.info(f"  → Re-collected {count} {kind} for {city_name}")

            label, relationship = self.LINK_TARGETS[kind]
            self.neo4j_loader.link_to_nearest_area(city_id, label, relationship)

    def verify_hotel_prices(self, repository, city_id: str, city_name: str, limit: int = None):
        """Web-search each hotel's current price (via PriceVerifier) and stamp the
        result onto its Hotel node. Takes a Repository instance from the caller
        rather than opening a second Neo4j connection — api/main.py already holds
        one in app.state. Paced with a delay between hotels since this is one
        search + one LLM call per hotel and free search APIs rate-limit on volume.

        `limit` caps how many hotels get (re-)verified in one call — verifying an
        entire city's worth of hotels can take minutes, so default callers (the
        /admin/refresh endpoint) should pass a sane cap rather than running
        unbounded by default."""
        from data.price_verifier import PriceVerifier

        hotels = repository.get_hotels(city_id, limit=limit or 1000)
        verifier = PriceVerifier()
        logger.info(f"  Verifying live prices for {len(hotels)} hotels in {city_name}...")

        verified = 0
        for i, hotel in enumerate(hotels):
            if i > 0:
                time.sleep(2)
            result = verifier.verify_hotel_price(hotel["name"], city_name)
            if self.neo4j_loader.update_verified_price(
                city_id, hotel["name"], result["price"], result["currency"], result["confidence"],
            ):
                verified += 1
                if result["price"] is not None:
                    logger.info(f"  → {hotel['name']}: {result['price']} {result['currency']} "
                                f"({result['confidence']} confidence)")

        logger.info(f"✓ Verified prices for {verified}/{len(hotels)} hotels in {city_name}")
        return verified

    def bootstrap_city(self, city_name: str, city_id: str):
        """
        Lightweight setup for a comparison city: city node + manual norms/areas
        only — skips OSM collection. Useful for seeding the "origin" side of a
        cross-city relationship (conflicts, similarities) before its full data
        pipeline has been run.
        """
        logger.info(f"\n[BOOTSTRAP] Setting up {city_name} (norms & areas only)...")
        self.create_city_node(city_name, city_id)
        self.load_manual_norms(city_id)
        self.load_manual_areas(city_id)

    def load_cross_city_edges(self):
        """
        Load manually curated CONFLICTS_WITH (between Norms) and SIMILAR_VIBE_TO
        (between Areas) edges. Requires both cities involved to already exist
        in the graph — run after each city has been loaded/bootstrapped.
        """
        logger.info(f"\n[CROSS-CITY] Loading conflict & similarity edges...")
        self.load_manual_conflicts()
        self.load_manual_similarities()

    # ============ CITY SETUP ============

    def create_city_node(self, city_name: str, city_id: str):
        """Create city node in Neo4j"""
        # Metadata for Indian cities
        city_metadata = {
            "ahmedabad": {
                "state": "Gujarat",
                "population": 8600000,
                "primary_language": "Gujarati",
                "safety_index": 7.5,
                "cost_index": 65,
                "description": "Financial and textile hub of Gujarat"
            },
            "bangalore": {
                "state": "Karnataka",
                "population": 11400000,
                "primary_language": "Kannada",
                "safety_index": 7.0,
                "cost_index": 100,
                "description": "Silicon Valley of India, IT capital"
            },
            "gwalior": {
                "state": "Madhya Pradesh",
                "population": 1100000,
                "primary_language": "Hindi",
                "safety_index": 8.0,
                "cost_index": 45,
                "description": "Historic city known for Gwalior Fort"
            }
        }

        metadata = city_metadata.get(city_id, {})
        city = City(
            id=city_id,
            name=city_name,
            state=metadata.get("state", ""),
            population=metadata.get("population", 0),
            primary_language=metadata.get("primary_language", "Hindi"),
            safety_index=metadata.get("safety_index", 7.0),
            cost_of_living_index=metadata.get("cost_index", 100),
            description=metadata.get("description", "")
        )

        self.neo4j_loader.create_city(city)

    # ============ ATTRACTIONS LOADING ============

    def load_attractions_to_neo4j(self, attractions: List[Place]):
        """Load attractions into Neo4j"""
        for i, attraction in enumerate(attractions):
            if self.neo4j_loader.create_place(attraction):
                if (i + 1) % 10 == 0:
                    logger.info(f"  ✓ Loaded {i + 1}/{len(attractions)} attractions")

        logger.info(f"✓ All {len(attractions)} attractions loaded to Neo4j")

    # ============ HOTELS LOADING ============

    def load_hotels_to_neo4j(self, hotels: List[Hotel]):
        """Load hotels into Neo4j"""
        for i, hotel in enumerate(hotels):
            if self.neo4j_loader.create_hotel(hotel):
                if (i + 1) % 10 == 0:
                    logger.info(f"  ✓ Loaded {i + 1}/{len(hotels)} hotels")

        logger.info(f"✓ All {len(hotels)} hotels loaded to Neo4j")

    # ============ RESTAURANTS LOADING ============

    def load_restaurants_to_neo4j(self, restaurants: List[Restaurant]):
        """Load restaurants into Neo4j"""
        for i, restaurant in enumerate(restaurants):
            if self.neo4j_loader.create_restaurant(restaurant):
                if (i + 1) % 10 == 0:
                    logger.info(f"  ✓ Loaded {i + 1}/{len(restaurants)} restaurants")

        logger.info(f"✓ All {len(restaurants)} restaurants loaded to Neo4j")

    # ============ MANUAL DATA LOADING ============

    def load_manual_norms(self, city_id: str):
        """Load manually curated norms from JSON"""
        fixture_file = self.data_dir / f"{city_id}_norms.json"

        if not fixture_file.exists():
            logger.warning(f"  ⚠️  Norms file not found: {fixture_file}")
            logger.info("  → Create it manually at: data/collected/{city_id}_norms.json")
            return

        try:
            with open(fixture_file, 'r') as f:
                norms_data = json.load(f)

            for norm_dict in norms_data:
                norm = Norm(**norm_dict)
                self.neo4j_loader.create_norm(norm)

            logger.info(f"✓ Loaded {len(norms_data)} norms for {city_id}")

        except Exception as e:
            logger.error(f"Error loading norms: {e}")

    def load_manual_areas(self, city_id: str):
        """Load manually curated areas from JSON"""
        fixture_file = self.data_dir / f"{city_id}_areas.json"

        if not fixture_file.exists():
            logger.warning(f"  ⚠️  Areas file not found: {fixture_file}")
            return

        try:
            with open(fixture_file, 'r') as f:
                areas_data = json.load(f)

            for area_dict in areas_data:
                # Reconstruct Coordinates object
                coords_data = area_dict.pop('coordinates')
                area_dict['coordinates'] = Coordinates(**coords_data)

                area = Area(**area_dict)
                self.neo4j_loader.create_area(area)

            logger.info(f"✓ Loaded {len(areas_data)} areas for {city_id}")

        except Exception as e:
            logger.error(f"Error loading areas: {e}")

    def load_manual_places(self, city_id: str):
        """Load hand-curated seed places — one representative per PlaceCategory,
        used to bootstrap full category coverage before bulk OSM data is collected"""
        fixture_file = self.data_dir / f"{city_id}_places_seed.json"

        if not fixture_file.exists():
            logger.warning(f"  ⚠️  Places seed file not found: {fixture_file}")
            return

        try:
            with open(fixture_file, 'r') as f:
                places_data = json.load(f)

            for place_dict in places_data:
                coords_data = place_dict.pop('coordinates')
                place_dict['coordinates'] = Coordinates(**coords_data)

                place = Place(**place_dict)
                self.neo4j_loader.create_place(place)

            logger.info(f"✓ Loaded {len(places_data)} seed places for {city_id}")

        except Exception as e:
            logger.error(f"Error loading seed places: {e}")

    def load_manual_conflicts(self):
        """Load manually curated CONFLICTS_WITH edges between cities' norms.
        Fixture is cross-city, so it lives at data/collected/conflicts.json
        rather than under a single city's prefix."""
        fixture_file = self.data_dir / "conflicts.json"

        if not fixture_file.exists():
            logger.warning(f"  ⚠️  Conflicts file not found: {fixture_file}")
            return

        try:
            with open(fixture_file, 'r') as f:
                conflicts_data = json.load(f)

            created = 0
            for c in conflicts_data:
                if self.neo4j_loader.create_conflict_edge(
                    norm1_id=c['norm1_id'],
                    norm2_id=c['norm2_id'],
                    conflict_type=c.get('conflict_type', 'taboo_in_dest'),
                    confidence=c.get('confidence', 0.85),
                    embarrassment_risk=c.get('embarrassment_risk', 7)
                ):
                    created += 1

            logger.info(f"✓ Loaded {created}/{len(conflicts_data)} conflict edges")

        except Exception as e:
            logger.error(f"Error loading conflicts: {e}")

    def load_manual_similarities(self):
        """Load manually curated SIMILAR_VIBE_TO edges between cities' areas.
        Fixture is cross-city, so it lives at data/collected/similarities.json
        rather than under a single city's prefix."""
        fixture_file = self.data_dir / "similarities.json"

        if not fixture_file.exists():
            logger.warning(f"  ⚠️  Similarities file not found: {fixture_file}")
            return

        try:
            with open(fixture_file, 'r') as f:
                similarities_data = json.load(f)

            created = 0
            for s in similarities_data:
                if self.neo4j_loader.create_similarity_edge(
                    area1_id=s['area1_id'],
                    area2_id=s['area2_id'],
                    similarity_score=s['similarity_score'],
                    shared_traits=s.get('shared_traits', [])
                ):
                    created += 1

            logger.info(f"✓ Loaded {created}/{len(similarities_data)} similarity edges")

        except Exception as e:
            logger.error(f"Error loading similarities: {e}")

    def load_manual_norm_contexts(self, city_id: str):
        """Load REQUIRES_CONTEXT edges that ground a city's norms in real
        places where they're actually observable (e.g. "Bargaining" -> Manek
        Chowk), so the agent can point travelers to go see it for themselves."""
        fixture_file = self.data_dir / f"{city_id}_norm_contexts.json"

        if not fixture_file.exists():
            logger.warning(f"  ⚠️  Norm contexts file not found: {fixture_file}")
            return

        try:
            with open(fixture_file, 'r') as f:
                contexts_data = json.load(f)

            created = 0
            for ctx in contexts_data:
                if self.neo4j_loader.create_requires_context_edge(
                    norm_id=ctx['norm_id'],
                    place_id=ctx['place_id'],
                    relevance=ctx.get('relevance', 'high'),
                    note=ctx.get('note', '')
                ):
                    created += 1

            logger.info(f"✓ Loaded {created}/{len(contexts_data)} norm-context edges for {city_id}")

        except Exception as e:
            logger.error(f"Error loading norm contexts: {e}")

    def load_manual_cost_of_living(self, city_id: str):
        """Load cost of living data from JSON into Neo4j as CostOfLiving nodes
        linked to the City — previously this only validated the JSON parsed
        without ever writing it to the graph, so the data was uncollectable."""
        fixture_file = self.data_dir / f"{city_id}_cost_of_living.json"

        if not fixture_file.exists():
            logger.warning(f"  ⚠️  Cost of living file not found: {fixture_file}")
            return

        try:
            with open(fixture_file, 'r') as f:
                items_data = json.load(f)

            created = 0
            for item_dict in items_data:
                item = CostOfLiving(
                    id=item_dict["id"],
                    city=item_dict["city"],
                    category=item_dict["category"],
                    item=item_dict["item"],
                    price_range=item_dict.get("price_range", {}),
                    neighborhood_breakdown=item_dict.get("neighborhood_breakdown", {}),
                    compared_to_city=item_dict.get("compared_to_city", ""),
                    parity_ratio=item_dict.get("parity_ratio", 1.0),
                )
                if self.neo4j_loader.create_cost_of_living_item(item):
                    created += 1

            logger.info(f"✓ Loaded {created}/{len(items_data)} cost-of-living items for {city_id}")

        except Exception as e:
            logger.error(f"Error loading cost of living: {e}")

    # ============ UTILITY FUNCTIONS ============

    def save_to_json(self, objects: List, filename: str):
        """Save collected objects to JSON for backup.

        Refuses to overwrite an existing non-empty backup with an empty result —
        an empty collection run (e.g. an OSM rate-limit that exhausted retries)
        would otherwise silently destroy a previously-good backup file."""
        try:
            filepath = self.data_dir / filename

            if not objects and filepath.exists() and filepath.stat().st_size > 2:
                logger.warning(f"  ⚠️  Skipping save to {filename}: collected 0 objects "
                               f"but an existing non-empty backup is present (not overwriting)")
                return

            # Convert dataclass objects to dicts
            data = []
            for obj in objects:
                if hasattr(obj, 'to_dict'):
                    data.append(obj.to_dict())
                else:
                    data.append(vars(obj))

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"✓ Saved {len(objects)} objects to {filename}")

        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")

    def close(self):
        """Close all connections"""
        self.neo4j_loader.close()
        logger.info("Pipeline closed")


if __name__ == '__main__':
    import sys

    # Validate environment
    required_vars = ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nCopy config.env.example to .env and fill in your credentials")
        sys.exit(1)

    pipeline = DataIngestionPipeline()

    try:
        # Run full pipeline (OSM collection + manual fixtures) for the
        # original 3-city scope from LOCAL_BUDDY_SYSTEM_DESIGN.md
        pipeline.run_full_pipeline("Ahmedabad, India", "ahmedabad")
        pipeline.run_full_pipeline("Mumbai, India", "mumbai")
        pipeline.run_full_pipeline("Gwalior, India", "gwalior")

        # Bootstrap Bangalore (norms + areas only, no OSM collection) so the
        # MVP "Bangalore -> Ahmedabad" cross-city edges below have real targets
        pipeline.bootstrap_city("Bangalore, India", "bangalore")

        # Load CONFLICTS_WITH (norms) and SIMILAR_VIBE_TO (areas) edges between them
        pipeline.load_cross_city_edges()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        pipeline.close()

    logger.info("\n✓ Data ingestion complete!")

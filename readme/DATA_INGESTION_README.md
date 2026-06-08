# Data Ingestion Pipeline - Local Buddy

Complete guide to collecting and loading city data into Neo4j knowledge graph.

## Quick Start (5 minutes)

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install python-dotenv neo4j googlemaps
```

### 2. Configure Credentials

```bash
# Copy example config
cp config.env.example .env

# Edit .env and add your credentials
# You need:
# - Google Maps API Key (from Google Cloud Console)
# - Neo4j connection details (from docker-compose)
```

### 3. Start Neo4j Database

```bash
# From project root
docker-compose up -d

# Verify it's running
curl http://localhost:7474  # Should show Neo4j UI
```

### 4. Run Data Ingestion

```bash
# From project root
python data/ingestion_pipeline.py
```

**Expected output:**
```
============================================================
STARTING PIPELINE FOR AHMEDABAD
============================================================

[STEP 1] Creating city node...
✓ City created: Ahmedabad

[STEP 2] Collecting attractions from Google Maps...
✓ Found 50 attractions

[STEP 3] Collecting hotels from Google Maps...
✓ Found 40 hotels

[STEP 4] Collecting restaurants from Google Maps...
✓ Found 55 restaurants

[STEP 5] Loading manual data from JSON fixtures...
✓ Loaded 5 norms for ahmedabad
✓ Loaded 4 areas for ahmedabad
✓ Cost of living data ready for ahmedabad

[SUMMARY] Ahmedabad pipeline complete!
City: Ahmedabad
  Areas: 4
  Attractions: 50
  Hotels: 40
  Restaurants: 55
  Norms: 5

✓ Data ingestion complete!
```

---

## Project Structure

```
data/
├── models.py                          # Data models (City, Area, Place, etc.)
├── ingestion_pipeline.py              # Main orchestrator
├── collectors/
│   └── google_maps_collector.py       # Google Places API fetcher
├── loaders/
│   └── neo4j_loader.py                # Neo4j insertion logic
└── collected/                         # Output & fixtures
    ├── ahmedabad_norms.json           # Manual norms data
    ├── ahmedabad_areas.json           # Manual areas data
    ├── ahmedabad_cost_of_living.json  # Cost comparisons
    └── [auto-generated JSON files from API calls]
```

---

## Data Models

### Core Entities

**City**
```python
{
  "id": "ahmedabad",
  "name": "Ahmedabad",
  "state": "Gujarat",
  "population": 8600000,
  "primary_language": "Gujarati",
  "safety_index": 7.5,
  "cost_of_living_index": 65,
  "description": "..."
}
```

**Area** (Neighborhood)
```python
{
  "id": "area_naranpura_ahmedabad",
  "name": "Naranpura",
  "city": "ahmedabad",
  "locality_type": "traditional_commercial",
  "coordinates": {"lat": 23.0225, "lng": 72.5714},
  "average_rent_1bhk": 20000,
  "lifestyle_tags": ["traditional", "markets", "gujarati_food"],
  "safety_level": "safe",
  "public_transport_score": 8,
  "walkability_score": 7
}
```

**Place** (Attraction)
```python
{
  "id": "taj_gateway_mumbai",
  "name": "Gateway of India",
  "city": "mumbai",
  "area": "colaba",
  "category": "historical",
  "coordinates": {"lat": 18.9220, "lng": 72.8347},
  "google_rating": 4.5,
  "entry_fee": {"local": 0, "foreign": 600},
  "must_visit": true
}
```

**Norm** (Cultural/Social Rule)
```python
{
  "id": "norm_bargaining_ahmedabad",
  "city": "ahmedabad",
  "title": "Bargaining in Markets",
  "category": "general",
  "description": "Bargaining is expected in markets...",
  "embarrassment_risk": 6,
  "prevalence": "common",
  "dos": ["Start at 60-70% of asking price"],
  "donts": ["Don't insult the goods"]
}
```

---

## API Integration

### Google Maps API Setup

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com
   - Create new project
   - Enable "Places API"
   - Enable "Maps SDK"

2. **Get API Key**
   - Go to Credentials
   - Create API Key
   - Restrict to "Application restriction" (IP address)
   - Restrict to "Places API" & "Maps SDK"

3. **Add to .env**
   ```
   GOOGLE_MAPS_API_KEY=your_actual_key_here
   ```

### What Data is Collected

| Endpoint | What's Fetched | Count |
|----------|---------------|-------|
| `places_nearby(keyword="tourist attraction")` | Attractions | 50 |
| `places_nearby(type="lodging")` | Hotels | 50 |
| `places_nearby(keyword="restaurant")` | Restaurants | 50 |

---

## Manual Data (Fixtures)

These aren't fetched from APIs - they're manually curated. See examples in `data/collected/`:

### ahmedabad_norms.json
Cultural norms specific to Ahmedabad
- Key conflicts with Bangalore
- Embarrassment risk scores
- Practical do's & don'ts

### ahmedabad_areas.json
Neighborhoods & localities
- Vibe characteristics
- Rent ranges
- Lifestyle tags
- Safety ratings

### ahmedabad_cost_of_living.json
Cost comparisons
- Rent by neighborhood
- Food prices
- Transport costs
- Parity ratios with Bangalore

**How to contribute:**
1. Edit these JSON files directly
2. Follow the schema (see examples)
3. Re-run pipeline with `python data/ingestion_pipeline.py`

---

## Database Queries

Once data is loaded, query Neo4j directly:

```cypher
# Get all attractions in Ahmedabad
MATCH (p:Place)-[:NORMAL_IN]->(c:City {id: "ahmedabad"})
RETURN p.name, p.category, p.google_rating
ORDER BY p.google_rating DESC
LIMIT 10;

# Find similar areas between cities
MATCH (a1:Area {id: "area_naranpura_ahmedabad"})
MATCH (a2:Area {city: "bangalore"})
WHERE vector_similarity(a1.vibe, a2.vibe) > 0.7
RETURN a1.name, a2.name, similarity;

# Get conflict norms
MATCH (n1:Norm)-[:NORMAL_IN]->(c1:City {id: "bangalore"})
MATCH (n1)-[:CONFLICTS_WITH]->(n2:Norm)
WHERE (n2)-[:NORMAL_IN]->(c2:City {id: "ahmedabad"})
RETURN n1.title, n2.title, n2.embarrassment_risk
ORDER BY n2.embarrassment_risk DESC;
```

---

## Troubleshooting

### Error: "No place_id found"
→ Google Maps API might be rate-limited or not returning results
→ Solution: Check API key is valid, quotas not exceeded

### Error: "Connection refused" (Neo4j)
→ Neo4j container isn't running
→ Solution: `docker-compose up -d` and wait 5 seconds

### Error: "GOOGLE_MAPS_API_KEY not set"
→ Missing .env file
→ Solution: `cp config.env.example .env` and fill in credentials

### Only getting 5-10 results instead of 50?
→ API hitting rate limits (60 requests/minute)
→ Solution: Split collection across hours or use pagination

---

## Next Steps

After running pipeline for Ahmedabad:

1. **Add Bangalore data**
   ```bash
   pipeline.run_full_pipeline("Bangalore, India", "bangalore")
   ```

2. **Create conflict edges** (manually)
   ```python
   loader.create_conflict_edge(
       norm1_id="norm_bargaining_bangalore",
       norm2_id="norm_bargaining_ahmedabad",
       confidence=0.92,
       embarrassment_risk=8
   )
   ```

3. **Create similarity edges** (between areas)
   ```python
   loader.create_similarity_edge(
       area1_id="area_indiranagar_bangalore",
       area2_id="area_naranpura_ahmedabad",
       similarity_score=0.72,
       shared_traits=["trendy", "cafes", "young_professionals"]
   )
   ```

4. **Query the graph** from your API endpoints

---

## Architecture

```
Google Maps API
       ↓
GoogleMapsCollector (fetches data)
       ↓
data_ingestion_pipeline.py (orchestrates)
       ↓
Neo4jLoader (inserts into database)
       ↓
Neo4j Graph Database (stores relationships)
       ↓
Your Agents (query for insights)
```

---

## Performance Notes

- **Total data per city**: ~150 nodes
- **Collection time**: 2-3 minutes (including API calls)
- **Loading time**: 30-60 seconds
- **Database size**: ~1MB per city (300MB for 300 cities)

To speed up:
- Increase `GOOGLE_PLACES_RESULTS_LIMIT` in .env
- Run pipelines in parallel (different processes)
- Cache Google API responses

---

## Contributing Data

1. **Find inaccuracy** in collected data? Edit the JSON file directly
2. **Want to add more norms?** Add to `ahmedabad_norms.json`
3. **Know a hidden gem?** Add to `ahmedabad_areas.json`

Submit PR with updated fixtures - they'll be auto-loaded on next run.

---

**Questions?** Check IDEA.md or BUILD_SUMMARY.md for more context.

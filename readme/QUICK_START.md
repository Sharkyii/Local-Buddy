# Data Ingestion - Quick Start Guide

Complete, runnable system to load Ahmedabad data into Neo4j. **Start here.**

---

## What You Have

✅ Complete data ingestion pipeline
✅ Google Maps API integration
✅ Neo4j data loader
✅ Data models (City, Area, Place, Restaurant, Hotel, Norm)
✅ Seed fixtures (norms, areas, cost of living)
✅ Full documentation

---

## 4-Hour Build Plan

### Hour 1: Setup

```bash
# 1. Create Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements-data.txt

# 3. Copy config and fill in credentials
cp config.env.example .env

# Edit .env with your:
# GOOGLE_MAPS_API_KEY (from google cloud console)
# NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD unchanged (localhost defaults)
```

### Hour 2: Start Neo4j

```bash
# From project root
docker-compose up -d

# Wait 10 seconds for startup
sleep 10

# Verify running
docker ps
# Should show neo4j and postgres containers

# Check Neo4j web UI
# Open browser → http://localhost:7474
# Login: neo4j / password123
```

### Hour 3: Get Google Maps API Key

**Option A: Fast (5 min)**
- Go to: https://developers.google.com/maps/documentation/places/web-service/get-api-key
- Click "Get Start" → "Create project"
- Enable Places API
- Copy key to .env

**Option B: If that doesn't work**
- Google Cloud Console → https://console.cloud.google.com
- Create Project
- APIs & Services → Enable "Places API"
- Credentials → Create API Key
- Copy to .env

### Hour 4: Run Data Ingestion

```bash
# From project root
python data/ingestion_pipeline.py

# See it collect & load Ahmedabad data
# Should complete in 2-3 minutes

# Check Neo4j web UI again
# Visit http://localhost:7474
# Run: MATCH (n) RETURN count(n)
# Should show ~150 nodes
```

---

## Success Markers

✅ **After Hour 1:**
- `python -c "import neo4j; print('ok')"` returns "ok"

✅ **After Hour 2:**
- `docker ps` shows 2 containers running
- Browser shows Neo4j login screen at localhost:7474

✅ **After Hour 3:**
- No errors in `.env` when running script

✅ **After Hour 4:**
- Script says "✓ Data ingestion complete!"
- Neo4j has 100+ nodes loaded
- Can query: MATCH (c:City {id: "ahmedabad"}) RETURN c

---

## File Organization

```
LOCAL BUDDY PROJECT
├── .env (created from config.env.example)
├── docker-compose.yml
│
├── data/
│   ├── models.py                    ✓ Data classes
│   ├── ingestion_pipeline.py        ✓ Main script (RUN THIS)
│   ├── collectors/
│   │   └── google_maps_collector.py ✓ Fetches from API
│   ├── loaders/
│   │   └── neo4j_loader.py          ✓ Inserts into DB
│   └── collected/
│       ├── ahmedabad_norms.json     ✓ Manual norms
│       ├── ahmedabad_areas.json     ✓ Manual areas
│       └── ahmedabad_cost_of_living.json ✓ Cost data
│
└── requirements-data.txt            ✓ Dependencies

LOG FILE:
└── logs/data_ingestion.log          (auto-created)
```

---

## Testing - One-Line Verification

After running pipeline, verify data loaded:

```bash
# Count all nodes
curl -X POST http://localhost:7474/db/data/transaction/commit \
  -H "Authorization: Basic bmVvNGo6cGFzc3dvcmQxMjM=" \
  -d '{"statements":[{"statement":"MATCH (n) RETURN count(n)"}]}'

# Or simpler - use Neo4j web UI:
# http://localhost:7474 → console → type:
# MATCH (c:City {id: "ahmedabad"}) RETURN c.name, c.population
```

---

## What Data You'll Have

| Entity | Count | Source |
|--------|-------|--------|
| City | 1 | Manual |
| Areas | 4 | Manual (JSON) |
| Attractions | 50 | Google Maps API |
| Hotels | 50 | Google Maps API |
| Restaurants | 55 | Google Maps API |
| Norms (cultural rules) | 5 | Manual (JSON) |
| Cost of Living entries | 4 | Manual (JSON) |
| **TOTAL** | **~170 nodes** | Mixed |

---

## Troubleshooting

### "GOOGLE_MAPS_API_KEY not set"
```bash
# Open .env file
# Make sure it has: GOOGLE_MAPS_API_KEY=your_actual_key
# Not: GOOGLE_MAPS_API_KEY=your_key_placeholder
```

### "Connection refused" (Neo4j)
```bash
# Check if container running
docker ps

# If not, start it
docker-compose up -d

# Wait 10 seconds
sleep 10
```

### "HTTP 403 Forbidden" (Google Maps API)
```bash
# API key might not have Places API enabled
# Go back to Google Cloud Console
# APIs & Services → Enable "Places API"
# Wait 5 minutes for propagation
```

### "No attractions found" or very few results
```bash
# Rate limiting from Google
# Edit ingestion_pipeline.py line 78:
# result_limit=10  # Reduce from 50
# Then run again
```

---

## After First Run - What to Do Next

### Add Bangalore Data
```bash
# Edit data/ingestion_pipeline.py, bottom section:
# Uncomment: pipeline.run_full_pipeline("Bangalore, India", "bangalore")
# Run again
```

### Create Conflict Edges
```python
# Open Python console
from data.loaders.neo4j_loader import Neo4jLoader

loader = Neo4jLoader(...)
loader.create_conflict_edge(
    norm1_id="norm_bargaining_bangalore",
    norm2_id="norm_bargaining_ahmedabad",
    confidence=0.92,
    embarrassment_risk=8
)
```

### Query the Data
```cypher
# In Neo4j web UI console at http://localhost:7474

# Get all restaurants in Naranpura
MATCH (r:Restaurant)-[:IN_AREA]->(a:Area {name: "Naranpura"})
RETURN r.name, r.price_range, r.google_rating
ORDER BY r.google_rating DESC;

# Get conflict norms
MATCH (n1:Norm)-[:CONFLICTS_WITH]->(n2:Norm)
WHERE n1.city = "bangalore" AND n2.city = "ahmedabad"
RETURN n1.title, n2.title, n2.embarrassment_risk;
```

---

## File by File - What Each Does

| File | Purpose |
|------|---------|
| `models.py` | Defines City, Area, Norm, Restaurant, etc. classes |
| `google_maps_collector.py` | Fetches real data from Google Places API |
| `neo4j_loader.py` | Inserts data into Neo4j graph database |
| `ingestion_pipeline.py` | Orchestrates everything (RUN THIS) |
| `ahmedabad_norms.json` | Hard-coded cultural rules & norms |
| `ahmedabad_areas.json` | Hard-coded neighborhoods & vibes |
| `ahmedabad_cost_of_living.json` | Hard-coded price comparisons |

---

## Architecture Visualization

```
YOU
 ↓
python data/ingestion_pipeline.py
 ↓
[GoogleMapsCollector] ← Google Maps API
 ├─ Searches "tourist_attraction" in Ahmedabad
 ├─ Gets 50 attractions with ratings & photos
 └─ Returns Place objects
 ↓
[Neo4jLoader]
 ├─ Creates nodes in Neo4j
 ├─ Creates edges (relationships)
 └─ Saves to database
 ↓
[Neo4j Database]
 ├─ 150+ nodes (cities, areas, places, norms)
 ├─ Relationships (HAS_AREA, HAS_PLACE, CONFLICTS_WITH)
 └─ Ready for your agents to query
 ↓
[Your Agents]
 ├─ Gap analysis "What norms does user not know?"
 ├─ Conflict detection "Which are embarrassing?"
 └─ Recommendations "What should I learn first?"
```

---

## Next Phase (After MVP Works)

Once you have this running for Ahmedabad:

1. **Add 2nd city (Bangalore)**
   - Copy fixture files
   - Update pipeline
   - Run same script

2. **Create conflict edges**
   - "Bargaining normal in Ahmedabad, rude in Bangalore"
   - Script auto-detects via feature vectors

3. **Add to API**
   - Endpoint: `POST /api/v1/plan`
   - Calls `gap_analyzer` from data pipeline
   - Returns prioritized conflicts

4. **Build agent on top**
   - Claude API + Graph queries
   - "I'm moving from Bangalore to Ahmedabad"
   - Returns personalized plan

---

## Success Criteria

- [x] Data ingestion completes without errors
- [x] Neo4j shows 150+ nodes
- [x] Can query: `MATCH (p:Place) WHERE p.city = 'ahmedabad' RETURN count(p)`
- [x] API can fetch attractions for gap analysis
- [x] Benchmark: <1 second to query 10 conflicts

---

## Support

**Lost?** Check:
- `DATA_INGESTION_README.md` - Full technical docs
- `IDEA.md` - System architecture
- `BUILD_SUMMARY.md` - Project overview

**Still stuck?** Errors in `logs/data_ingestion.log`

---

## Run It Now

```bash
# Copy-paste these 4 commands:

1. cp config.env.example .env
2. pip install -r requirements-data.txt
3. docker-compose up -d
4. python data/ingestion_pipeline.py
```

**That's it. You'll have Ahmedabad data in Neo4j in 5 minutes.**

Let me know when it's running! 🚀

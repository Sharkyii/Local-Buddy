# Local Buddy

An AI travel/relocation companion for Indian cities. Real city data (OpenStreetMap +
hand-curated fixtures) lives in a Neo4j graph; a multi-agent chatbot (local LLM via
Ollama, or Claude/Groq if you have a key) answers questions grounded in that data —
attractions, food, hotels, safety, local customs, and relocation comparisons between
cities.

## Architecture

```
React (web) ──┐
React Native ─┼──► FastAPI (api/main.py) ──► Orchestrator ──► 5 domain agents
                         │                                     (travel/food/culture/
                         │                                      safety/relocation)
                         ▼                                          │
                  Redis (chat memory)                               ▼
                  - Chat History                              Repository (read-only
                  - Session Memory                             Cypher queries)
                  - User Memory                                      │
                                                                      ▼
                                                                  Neo4j graph
                                                                      ▲
                                                                      │
                                          data/ingestion_pipeline.py ┘
                                          (OpenStreetMap + JSON fixtures)
```

- **Neo4j**: `City -[:HAS_AREA]-> Area -[:HAS_PLACE/HOTEL/RESTAURANT]->`, plus
  `CostOfLiving`, `Norm` (with cross-city `CONFLICTS_WITH`/`SIMILAR_VIBE_TO` edges).
  Every Place/Hotel/Restaurant has real GPS coordinates from OSM and gets linked to
  its geographically nearest Area (not by name matching).
- **Redis**: three memory layers per chat — full transcript, a bounded recent-turns
  window actually fed to the LLM, and durable cross-session facts about a person
  (e.g. "vegetarian") that the orchestrator notes via a tool call.
- **Agents** (`agents/`): one `BaseAgent` class runs a manual tool-use loop through
  LiteLLM, so the same code drives a local Ollama model, Claude, or Groq depending on
  what's configured. An orchestrator routes a question to the right specialist(s) and
  synthesizes their answers.
- **Reranker** (`data/reranker.py`): combines rating, distance, importance, and
  uniqueness into one score per result, with a plain-English reason for the ranking.

## Prerequisites

- Docker (for Neo4j + Redis)
- Python 3.12 + a venv (Debian/Ubuntu block `pip install --user` outside one)
- Node 18+ (for the web and mobile frontends)
- [Ollama](https://ollama.com) if running fully local (no API key needed), **or** an
  `ANTHROPIC_API_KEY` / `GROQ_API_KEY`

## Setup

### 1. Environment variables

Copy `data/.env` (already present in this repo) and review it — at minimum it needs:

```
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your password>
REDIS_URL=redis://localhost:6379/0
ADMIN_API_KEY=<any random string — protects POST /admin/refresh>

# Pick ONE model source:
OLLAMA_MODEL=ollama_chat/qwen2.5:3b-instruct   # fully local, free, no key
# ANTHROPIC_API_KEY=sk-ant-...                  # preferred if you have one
# GROQ_API_KEY=gsk_...                          # free tier fallback
```

`_select_model()` in `agents/base_agent.py` prefers `OLLAMA_MODEL` (explicit
override) > `ANTHROPIC_API_KEY` > `GROQ_API_KEY`. Comment out `OLLAMA_MODEL` to fall
back to a cloud model.

If you skip `ADMIN_API_KEY`, the backend generates a random one each restart and logs
it — fine for solo local dev, but set it explicitly so it doesn't change every time
you restart the server.

### 2. Start Neo4j + Redis

```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/<password> neo4j:5
docker run -d --name redis -p 6379:6379 redis:7

# Keeps them coming back on their own if they crash or the host reboots —
# do this once, it persists:
docker update --restart unless-stopped neo4j redis
```

### 3. Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-data.txt -r requirements-api.txt
```

### 4. (Local model only) Pull an Ollama model

```bash
ollama pull qwen2.5:3b-instruct
```

A non-reasoning, small instruct model. We tried `qwen3:8b` first — its `<think>`
trace made every reply 60-90s+. `qwen2.5:3b` answers directly and is much lighter on
RAM, at the cost of less reliable tool-use (see **Known limitations** below).

### 5. Load some city data

```bash
.venv/bin/python3 -c "
from dotenv import load_dotenv
load_dotenv('data/.env')
from data.ingestion_pipeline import DataIngestionPipeline
pipeline = DataIngestionPipeline()
pipeline.run_full_pipeline('Ahmedabad, India', 'ahmedabad')
pipeline.close()
"
```

This pulls attractions/hotels/restaurants from OpenStreetMap (free, no key), loads
hand-curated areas/norms/cost-of-living from `data/collected/*.json`, links
everything to its nearest area by real GPS distance, and self-heals any gaps left by
an OSM rate-limit. Safe to re-run — everything `MERGE`s, nothing duplicates.

Currently loaded: **Ahmedabad** (full data), **Gwalior** (full data), **Mumbai**
(partial — hotels/restaurants are stale, only attractions got the latest categories),
**Bangalore** (norms/areas only, no real OSM data yet).

## Running it

```bash
# Backend (from project root)
.venv/bin/uvicorn api.main:app --reload --app-dir .

# Web frontend
cd frontend && npm install && npm run dev          # http://localhost:5173

# Mobile scaffold (one chat screen, proves the path works — not a full port)
cd mobile && npm install && npx expo start --web    # http://localhost:19006
```

Neo4j Browser: `http://localhost:7474`. A custom style lives at
`data/neo4j_browser_style.grass`.

## Adding / refreshing data

`POST /admin/refresh` (needs the `X-Admin-Key` header):

```bash
curl -X POST http://127.0.0.1:8000/admin/refresh \
  -H "Content-Type: application/json" -H "X-Admin-Key: <your key>" \
  -d '{"city_id":"ahmedabad","city_name":"Ahmedabad, India","scope":"all"}'
```

`scope`:
- `"all"` — full pipeline (attractions + hotels + restaurants + area linking)
- `"attractions"` / `"hotels"` / `"restaurants"` — just one OSM category
- `"verify_prices"` — web-search + LLM-extract current hotel prices, writes a
  timestamped `verified_price` onto each Hotel node (pass `"limit": N` to cap how
  many hotels get checked — verifying a whole city takes minutes)

A scheduled job (`api/main.py`, APScheduler) also re-runs the full pipeline for every
city with real data, daily at 3 AM server-local time — no need to remember to call
this manually for routine upkeep.

For things OpenStreetMap doesn't have (areas, norms, cost-of-living, hand-picked seed
places): edit the matching `data/collected/<city_id>_<thing>.json` file, then call
the matching `load_manual_*` method on `DataIngestionPipeline` (see
`data/ingestion_pipeline.py`).

## Key API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /chat/sessions` | Start a conversation — `{city_id, user_id}` → `{session_id}` |
| `POST /chat/message` | `{session_id, message, lat?, lng?}` → `{reply}` (rate-limited, 20/min/IP) |
| `GET /chat/sessions/{id}/history` | Full transcript for a session |
| `GET /map/markers?city_id=...` | Every place/hotel/restaurant/area with coordinates |
| `POST /admin/refresh` | Trigger data collection (needs `X-Admin-Key`, 5/hour/IP) |

## Known limitations

- **The local model (`qwen2.5:3b`) has a real reasoning ceiling.** It sometimes calls
  the wrong tool, fabricates a detail when a tool result is empty, or follows a
  multi-step instruction inconsistently. We've patched the worst, most visible cases
  (e.g. forbidding it from naming any place a tool didn't literally return), but this
  is a model-size limitation, not a bug — switching to `ANTHROPIC_API_KEY` removes
  it entirely if you have a key.
- **OpenStreetMap has no pricing or rental-listing data.** `check_live_price` (a free
  web-search tool) covers this live instead of storing a number that'd go stale.
- **Cross-city relocation comparisons** (`agents/relocation_agent.py`) only have
  curated data for Bangalore↔Ahmedabad. Any other city pair gets just the generic
  cost-of-living/safety-index comparison.
- **Bangalore has no real place data** — only bootstrapped with norms/areas.
- **React Native is a scaffold**, not a full port — one hardcoded-city chat screen,
  no map, no live geolocation yet.

## Troubleshooting

- **`neo4j.exceptions.ConfigurationError: URI scheme b'' is not supported`** — your
  `.env` isn't loading. `load_dotenv()` with no argument searches upward from the
  current directory, not into subdirectories — if you run uvicorn from the project
  root, it won't find `data/.env` on its own. `api/main.py` already points
  `load_dotenv()` at the file explicitly; if you write a new script that touches
  Neo4j, do the same.
- **Docker containers (`neo4j`/`redis`) silently stop** — happened repeatedly during
  development on a RAM-constrained machine. `docker update --restart unless-stopped
  neo4j redis` (see Setup) makes Docker bring them back on its own.
- **Overpass (OSM) returns fewer results than expected, or a `406`/timeout** — it's a
  shared free public API and rate-limits under load. The collector already retries
  with backoff; if it's still short, just retry the `/admin/refresh` call a bit later.
- **A chat reply takes 30-90+ seconds** — expected on the local model. One question
  can mean 3-5 sequential LLM calls (orchestrator → sub-agent → its own tool loop →
  orchestrator synthesis). `/tmp/uvicorn.log` logs a per-call timing breakdown
  (`grep -E "\[orchestrator\]|\[travel_agent\]|\[api\]"`) if you need to see where
  the time actually goes.

# LOCAL BUDDY - Complete System Design & Architecture

**Project**: Local Buddy - AI Travel Companion App
**Scope**: 3 Indian Cities (Mumbai, Ahmedabad, Gwalior)
**Technology**: Python Backend, English Language
**Version**: 1.0 - Foundation Architecture
**Last Updated**: 2026-06-06

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [City Data Structure](#city-data-structure)
3. [End-to-End Data Flow](#end-to-end-data-flow)
4. [Real-Time Features Integration](#real-time-features-integration)
5. [Data Gathering Strategy](#data-gathering-strategy)
6. [Python Backend Architecture](#python-backend-architecture)
7. [Implementation Roadmap](#implementation-roadmap)

---

## OVERVIEW

### Project Vision
Local Buddy is an AI-powered travel companion that helps tourists and travelers from around the world integrate into new environments and become part of local culture. The system uses multi-agent AI architecture to provide:

- **Travel Planning**: Best places, routes, accommodation
- **Food Recommendations**: Restaurants, street food, local cuisine
- **Cultural Education**: History, traditions, festivals, etiquette
- **Safety Guidance**: Gender safety, traffic, theft prevention
- **Language Assistance**: Translations, phrases, accent guidance

### Current Scope
- **Cities**: Mumbai, Ahmedabad, Gwalior
- **Language**: English (Primary)
- **Platform**: Backend API + Chat Interface
- **Core Technology**: Claude API + Python

### Key Objectives
1. Provide contextual, city-specific travel advice
2. Educate travelers about local culture respectfully
3. Ensure traveler safety across diverse scenarios
4. Build confidence for travelers to explore authentically
5. Create seamless integration into local life

---

## CITY DATA STRUCTURE

### 1.1 Core Data Models

#### CityCore
```
CityCore:
  - city_id: str (ahmedabad, gwalior, mumbai)
  - name: str
  - state: str
  - language: str (Hindi/Gujarati/Marathi)
  - currency: str (INR)
  - timezone: str (IST)
  - population: int
  - best_visit_season: str
  - average_budget_per_day: dict {economy, moderate, premium}
  - description: str (150+ words about city)
```

#### Attraction
```
Attraction:
  - attraction_id: str (unique)
  - city_id: str
  - name: str
  - category: str (historical, religious, museum, park, market, etc.)
  - description: str (200+ words)
  - history: str (historical background)
  - timings: dict {opens: "HH:MM", closes: "HH:MM", closed_days: list}
  - entry_fee: dict {local: int, foreign: int, child: int, free: bool}
  - duration_to_visit: str (1 hour, 2-3 hours, full day)
  - accessibility: dict {wheelchair: bool, parking: bool, washrooms: bool}
  - coordinates: dict {lat: float, lng: float}
  - distance_from_city_center: float (km)
  - images: list (URLs)
  - best_time_to_visit: str
  - crowd_level: str (low, moderate, high)
  - must_visit_reason: str
```

#### Restaurant
```
Restaurant:
  - restaurant_id: str
  - city_id: str
  - name: str
  - cuisine_type: list (Indian, Gujarati, Street Food, etc.)
  - specialties: list (flagship dishes)
  - price_range: str (budget <200, moderate 200-500, premium >500)
  - ratings: dict {google: float, zomato: float, local_buddy: float}
  - vegetarian_options: bool
  - vegan_options: bool
  - allergen_info: dict {nuts: bool, dairy: bool, gluten: bool}
  - timings: dict {opens: "HH:MM", closes: "HH:MM", break_time: list}
  - coordinates: dict {lat: float, lng: float}
  - popular_dishes: list (with prices)
  - average_cost_per_person: int (INR)
  - ambiance: str (casual, formal, family-friendly, romantic)
  - reservation_needed: bool
  - contact: dict {phone: str, website: str}
```

#### Hotel
```
Hotel:
  - hotel_id: str
  - city_id: str
  - name: str
  - stars: int (1-5)
  - area: str
  - price_range: str
  - price_per_night: dict {economy: int, standard: int, premium: int}
  - amenities: list (WiFi, AC, breakfast, gym, pool, etc.)
  - specialties: list (unique experiences/themes)
  - accessibility: dict {wheelchair: bool, elevators: bool}
  - coordinates: dict {lat: float, lng: float}
  - contact: dict {phone: str, email: str, website: str}
  - check_in_time: str
  - check_out_time: str
  - cancellation_policy: str
  - images: list (URLs)
```

#### LocalPhrase
```
LocalPhrase:
  - phrase_id: str
  - city_id: str
  - english: str
  - local_language: str
  - phonetic: str (pronunciation guide)
  - situation: str (greeting, direction, help, bargaining, restaurant)
  - formal_level: str (formal, informal, casual)
  - usage_context: str (when/how to use)
  - example_usage: str
```

#### CulturalInfo
```
CulturalInfo:
  - info_id: str
  - city_id: str
  - title: str
  - category: str (history, festival, etiquette, tradition, art)
  - content: str (detailed information)
  - associated_places: list (location_ids)
  - dates: dict {if festival: month, duration}
  - importance_level: str (major, moderate, local)
  - dos: list (5-10 items)
  - donts: list (5-10 items)
  - impact_on_travel: str (how it affects visitor experience)
```

#### SafetyGuideline
```
SafetyGuideline:
  - guideline_id: str
  - city_id: str
  - category: str (women_safety, traffic, theft, health, emergency)
  - title: str
  - severity: str (critical, important, helpful)
  - content: str (practical advice)
  - traveler_type: str (all, women, solo, families, lgbtq)
  - location_specific: bool
  - hotspot_areas: list (if applicable)
  - emergency_contacts: dict {police: str, ambulance: str, tourist_police: str}
  - prevention_tips: list (5-10 items)
```

#### RealTimeData
```
RealTimeData:
  - data_id: str
  - city_id: str
  - data_type: str (weather, traffic, event, holiday)
  - timestamp: datetime
  - content: dict (structure varies by type)
  - ttl: int (time-to-live in seconds)
  - source: str (API endpoint or service)
  - last_updated: datetime
```

---

## END-TO-END DATA FLOW

### 2.1 User Request Flow - Complete Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (Traveler)                         │
│              "I'm arriving in Mumbai in 3 days                  │
│               for 1 week. Vegetarian, solo travel."             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                   REQUEST LAYER
                           │
        ┌──────────────────▼──────────────────┐
        │  API Gateway (Python FastAPI)       │
        │  - Validate request                 │
        │  - Extract user context             │
        │  - Create session                   │
        │  - Rate limiting check              │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  Context Manager                    │
        │  - User profile:                    │
        │    * Duration: 7 days               │
        │    * Preferences: Vegetarian        │
        │    * Traveler type: Solo            │
        │    * Budget: Unknown                │
        │  - Session state                    │
        │  - Chat history                     │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  Intent Classification (Claude API) │
        │  → Detect primary intent:           │
        │    • travel_planning (70%)          │
        │    • food_recommendations (15%)     │
        │    • culture_query (10%)            │
        │    • safety_query (5%)              │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  Orchestrator Agent Execution       │
        │                                    │
        │  Input:                            │
        │  - Original user message           │
        │  - User context (preferences)      │
        │  - City knowledge base             │
        │  - Real-time data (weather, etc.)  │
        │  - Chat history                    │
        │                                    │
        │  Process:                          │
        │  - Analyze all available data      │
        │  - Route to sub-agents             │
        │  - Synthesize comprehensive ans.   │
        └──────────────────┬──────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
┌───▼──────┐         ┌────▼────┐         ┌──────▼──────┐
│ TRAVEL   │         │ FOOD    │         │ CULTURE     │
│ AGENT    │         │ AGENT   │         │ AGENT       │
└───┬──────┘         └────┬────┘         └──────┬──────┘
    │                     │                     │
    │ Query:              │ Query:               │ Query:
    │ "Create optimal     │ "Find vegetarian    │ "What should
    │  7-day itinerary"   │  restaurants near   │  solo travelers
    │                     │  these attractions" │  know about
    │                     │                     │  Mumbai culture?"
    │                     │                     │
    └──────┬──────────────┼──────────────────────┘
           │              │              │
      ┌────▼──────────────▼──────────────▼────┐
      │  DATABASE QUERIES (MongoDB/PostgreSQL) │
      │                                       │
      │  Travel Agent Queries:                │
      │  - SELECT * FROM attractions         │
      │    WHERE city_id='mumbai'            │
      │    && category IN [museum, temple..] │
      │    && duration_to_visit <= 3 hours   │
      │    ORDER BY ratings DESC             │
      │                                       │
      │  Food Agent Queries:                  │
      │  - SELECT * FROM restaurants         │
      │    WHERE city_id='mumbai'            │
      │    && vegetarian_options=true        │
      │    && price_range IN [budget, mod.]  │
      │    ORDER BY ratings DESC             │
      │                                       │
      │  Culture Agent Queries:               │
      │  - SELECT * FROM cultural_info       │
      │    WHERE city_id='mumbai'            │
      │    ORDER BY importance_level DESC    │
      └────┬──────────────┬──────────────────┘
           │              │
      ┌────▼──────────────▼──────────────┐
      │  REAL-TIME DATA ENRICHMENT       │
      │                                  │
      │  Weather Service:                │
      │  - Current temp: 32°C            │
      │  - Humidity: 85%                 │
      │  - Rain forecast: 20% (next 7d)  │
      │                                  │
      │  Traffic Service:                │
      │  - Travel time hotel→attraction  │
      │  - Peak hours (9am, 6pm)         │
      │  - Public transit options        │
      │                                  │
      │  Events Service:                 │
      │  - Upcoming festivals            │
      │  - Street fairs/markets          │
      │  - Museum exhibitions            │
      │                                  │
      │  Safety Updates:                 │
      │  - Safety alerts by neighborhood │
      │  - Travel advisories             │
      │  - Health alerts                 │
      └────┬──────────────┬──────────────┘
           │              │
      ┌────▼──────────────▼──────────────┐
      │  FILTER & RANK RESULTS           │
      │                                  │
      │  Travel Agent Results:           │
      │  ✓ Gateway of India (3km away)   │
      │  ✓ Marine Drive (8km away)       │
      │  ✓ Chhatrapati Terminus (5km)    │
      │  ✓ Colaba Causeway (4km)         │
      │  [Ranked by relevance & distance]│
      │                                  │
      │  Food Agent Results:             │
      │  ✓ Restaurant A (veg, budget)    │
      │  ✓ Restaurant B (veg, moderate)  │
      │  ✓ Street food location C (veg)  │
      │  [Ranked by ratings & proximity] │
      │                                  │
      │  Culture Agent Results:          │
      │  ✓ Gateway of India history      │
      │  ✓ Colonial architecture guide   │
      │  ✓ Local festivals calendar      │
      │  [Ranked by relevance to stay]   │
      └────┬──────────────┬──────────────┘
           │              │
      ┌────▼──────────────▼──────────────┐
      │  RESPONSE SYNTHESIS              │
      │                                  │
      │  Claude API generates final      │
      │  integrated response that:       │
      │  - Combines all agent outputs    │
      │  - Adds cultural context         │
      │  - Personalizes to user profile  │
      │  - Cross-links related info      │
      │  - Adds safety warnings (if any) │
      │  - Provides budget breakdown     │
      │  - Optimizes timing              │
      │  - Suggests transportation       │
      └────┬──────────────┬──────────────┘
           │              │
      ┌────▼──────────────▼──────────────┐
      │  FORMAT RESPONSE                 │
      │                                  │
      │  - Markdown formatting           │
      │  - Include map links             │
      │  - Budget breakdown table        │
      │  - Day-by-day schedule           │
      │  - Restaurant booking links      │
      │  - Safety tips callouts          │
      │  - Cultural do's & don'ts        │
      └────┬──────────────┬──────────────┘
           │
   ┌───────▼────────────────────────────┐
   │ USER RECEIVES RESPONSE              │
   │                                    │
   │ "Here's your 7-day Mumbai plan..." │
   │                                    │
   │ DAY 1 ITINERARY:                   │
   │ - 9:00 AM: Gateway of India        │
   │ - 11:00 AM: Break for Chai         │
   │ - 12:00 PM: Chhatrapati Terminus   │
   │ - 2:00 PM: Lunch (Veg rest.)       │
   │ ... [continues]                    │
   │                                    │
   │ VEGETARIAN OPTIONS:                │
   │ - Restaurant A (nearby, ₹500)      │
   │ - Street food stall (₹100)         │
   │ ... [continues]                    │
   │                                    │
   │ CULTURAL TIPS:                     │
   │ - Gateway is symbol of Mumbai      │
   │ - Dress modestly at temples        │
   │ ... [continues]                    │
   │                                    │
   │ SAFETY NOTES:                      │
   │ ⚠️ Avoid Colaba at night (solo)    │
   │ ⚠️ Be careful with valuables       │
   │ ... [continues]                    │
   └────────────────────────────────────┘
```

### 2.2 Database Query Flow

```
REQUEST FROM AGENT
        │
        ▼
┌────────────────────────────┐
│ FILTER QUERY BUILDER       │
│                            │
│ Parameters:                │
│ - City: Mumbai             │
│ - Category: Attraction     │
│ - Distance: 5km            │
│ - Price: Budget            │
│ - Duration: < 3 hours      │
│ - Accessibility: Wheelchair│
└────────┬───────────────────┘
         │
    ┌────▼──────────────────┐
    │ DATABASE LAYER        │
    │ (MongoDB/PostgreSQL)  │
    │                       │
    │ Query Execution:      │
    │ - Connect to DB       │
    │ - Build WHERE clause  │
    │ - Execute query       │
    │ - Return result set   │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │ RESULT SET (1000+ recs)
    │                       │
    │ [Attraction results]  │
    │ - 47 matching records │
    │ - Raw from DB         │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │ FILTER ENGINE         │
    │                       │
    │ Apply rankings:       │
    │ - Geo-proximity (50%) │
    │ - Ratings (30%)       │
    │ - Popularity (20%)    │
    │                       │
    │ Result: Top 10        │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │ ENRICH WITH           │
    │ REAL-TIME DATA        │
    │                       │
    │ Add:                  │
    │ - Current weather     │
    │ - Traffic conditions  │
    │ - Event info          │
    │ - Latest reviews      │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │ FINAL RESULT SET      │
    │                       │
    │ [Enhanced results]    │
    │ - Ready for agent     │
    │ - Enriched with RTD   │
    │ - Ranked & filtered   │
    └────────────────────────┘
```

---

## REAL-TIME FEATURES INTEGRATION

### 3.1 Real-Time Data Sources

#### Weather Data
```
Source: OpenWeatherMap API / WeatherAPI.com
Update Frequency: Every 30 minutes
Data Points:
  - Current temperature
  - Weather forecast (7 days ahead)
  - Rainfall probability
  - UV index
  - Wind speed
  - Humidity levels

Usage in App:
  ✓ Recommend indoor attractions during extreme heat
  ✓ Suggest waterproof gear recommendations
  ✓ Warn about unsafe weather conditions (rain, storms)
  ✓ Optimize itinerary based on weather forecast
  ✓ Suggest best times for outdoor activities
```

#### Traffic & Transit Data
```
Source: Google Maps API / HERE Maps API
Update Frequency: Real-time (every 5 minutes)
Data Points:
  - Live traffic conditions
  - Estimated commute time between points
  - Public transit options & schedules
  - Alternative routes
  - Congestion patterns by hour

Usage in App:
  ✓ Optimize itinerary sequence (avoid traffic)
  ✓ Suggest travel times (peak vs. off-peak)
  ✓ Recommend public transit vs. taxi vs. walking
  ✓ Calculate accurate travel duration
  ✓ Provide cost estimates
```

#### Local Events & Festivals
```
Source: Local event aggregators + Manual curation
Update Frequency: Daily
Data Points:
  - Upcoming festivals & celebrations
  - Street fairs & temporary markets
  - Concerts, performances, exhibitions
  - Public holidays & closures
  - Special events this week

Usage in App:
  ✓ Recommend timely cultural experiences
  ✓ Warn about attraction closures
  ✓ Suggest event-specific day itineraries
  ✓ Update plan based on happenings
  ✓ Help catch unique opportunities
```

#### Restaurant Availability
```
Source: Zomato API / Google Places API
Update Frequency: Every 2 hours
Data Points:
  - Real-time availability
  - Current wait times
  - Live review updates
  - Delivery status
  - Special offers/deals
  - Peak hours

Usage in App:
  ✓ Real-time restaurant recommendations
  ✓ Avoid closed or temporarily full restaurants
  ✓ Suggest alternatives with short wait
  ✓ Update based on latest reviews
  ✓ Show current specials/deals
```

#### Safety Updates
```
Source: Local news + Police records (manual curation)
Update Frequency: Daily
Data Points:
  - Safety alerts by area/neighborhood
  - Crime reports (theft, incidents)
  - Traffic accident hotspots
  - Weather-related hazards
  - Health alerts (disease spread, etc.)

Usage in App:
  ✓ Dynamic safety warnings in itineraries
  ✓ Route recommendations avoiding unsafe areas
  ✓ Alert for specific traveler types (women, solo)
  ✓ Update safety guidelines in real-time
  ✓ Suggest safer alternatives
```

### 3.2 Real-Time Architecture

```
EXTERNAL APIs & DATA SOURCES
    │
    ├─→ OpenWeatherMap API
    ├─→ Google Maps API
    ├─→ Zomato API
    ├─→ Local event aggregators
    └─→ Local news feeds (RSS)
        │
        ▼
┌────────────────────────────────────┐
│  DATA INGESTION LAYER              │
│  (Python Background Jobs)          │
│                                    │
│  - Scheduled Fetchers (cron)       │
│  - Queue: Celery / APScheduler     │
│  - Error handling & retry logic    │
│  - Fallback to cached data         │
│  - Data validation & cleaning      │
└────────┬─────────────────────────────┘
         │
    ┌────▼──────────────┐
    │ CACHE LAYER       │
    │ (Redis)           │
    │                   │
    │ TTL Settings:     │
    │ - Weather: 30min  │
    │ - Traffic: 5min   │
    │ - Events: 24hr    │
    │ - Restaurants: 2hr│
    │ - Safety: 24hr    │
    │                   │
    │ Benefits:         │
    │ - Fast retrieval  │
    │ - Reduced API cost│
    │ - Fallback option │
    └────┬──────────────┘
         │
    ┌────▼──────────────────────┐
    │ QUERY INTERFACE LAYER     │
    │                           │
    │ When agent needs data:    │
    │ "What's current weather   │
    │  in Mumbai?"              │
    │                           │
    │ 1. Check Redis cache      │
    │ 2. If fresh → return      │
    │ 3. If stale/missing →     │
    │    Fetch from API         │
    │ 4. Cache new data         │
    │ 5. Return to agent        │
    └────┬──────────────────────┘
         │
    Response to Agent Queries
```

### 3.3 Background Job Configuration

```python
# Config: Real-time data refresh schedules

WEATHER_REFRESH_JOB:
  - Frequency: Every 30 minutes
  - Cities: [mumbai, ahmedabad, gwalior]
  - API: OpenWeatherMap
  - Timeout: 10 seconds
  - Retry: 3 attempts

TRAFFIC_REFRESH_JOB:
  - Frequency: Every 5 minutes
  - Cities: [mumbai, ahmedabad, gwalior]
  - API: Google Maps
  - Timeout: 15 seconds
  - Retry: 2 attempts

EVENTS_REFRESH_JOB:
  - Frequency: Once daily (6 AM IST)
  - Cities: [mumbai, ahmedabad, gwalior]
  - Source: Event aggregators + manual
  - Timeout: 30 seconds
  - Retry: 3 attempts

RESTAURANTS_REFRESH_JOB:
  - Frequency: Every 2 hours
  - Cities: [mumbai, ahmedabad, gwalior]
  - API: Zomato
  - Timeout: 20 seconds
  - Retry: 2 attempts
  - Batch size: 100 restaurants per batch

SAFETY_UPDATES_JOB:
  - Frequency: Once daily (8 AM IST)
  - Cities: [mumbai, ahmedabad, gwalior]
  - Source: Manual curation + news feeds
  - Timeout: 30 seconds
  - Retry: 1 attempt
```

---

## DATA GATHERING STRATEGY

### 4.1 City-Specific Data Collection

#### MUMBAI - Data Requirements

```
ATTRACTIONS (Target: 50-70)
├─ Historical Sites (10):
│  ├─ Gateway of India
│  ├─ Chhatrapati Shivaji Terminus
│  ├─ Mani Bhavan (Gandhi residence)
│  ├─ Colaba Causeway
│  └─ [6 more]
│
├─ Religious Sites (8):
│  ├─ Jagannath Mandir
│  ├─ Jama Masjid
│  ├─ Haji Ali Dargah
│  └─ [5 more]
│
├─ Museums & Culture (8):
│  ├─ Prince of Wales Museum
│  ├─ National Gallery of Modern Art
│  └─ [6 more]
│
├─ Parks & Natural (5):
│  ├─ Juhu Beach
│  ├─ Marine Drive
│  ├─ Hanging Gardens
│  └─ [2 more]
│
├─ Markets & Shopping (8):
│  ├─ Crawford Market
│  ├─ Linking Road
│  ├─ Bandra Fort Area
│  └─ [5 more]
│
└─ Modern Attractions (10+):
   ├─ Dharavi Slum Tours
   ├─ Bandra Worli Sea Link
   └─ [8+ more]

Data Points per Attraction:
  ✓ Name, category, description (200+ words)
  ✓ Full history & significance
  ✓ Exact hours (Mon-Sun, holidays)
  ✓ Entry fees (local, foreign, discounts)
  ✓ Duration to visit (1hr, 2-3hrs, full day)
  ✓ Accessibility info (wheelchair, parking, washroom)
  ✓ Precise coordinates (GPS)
  ✓ Distance from city center
  ✓ High-res images (3-5 per location)
  ✓ Best times to visit (seasonal, time of day)
  ✓ Crowd levels by time
  ✓ Why it's a must-visit

RESTAURANTS (Target: 100+)
├─ Maharashtrian Cuisine (15):
│  ├─ Dal Rice joints
│  ├─ Vada Pav counters
│  └─ [13 more]
│
├─ North Indian (12):
│  ├─ Mughlai restaurants
│  └─ [11 more]
│
├─ Gujarati Food (8):
│  ├─ Dhokla houses
│  └─ [7 more]
│
├─ Street Food Locations (20):
│  ├─ Pav Bhaji stalls
│  ├─ Dosa counters
│  ├─ Chaat centers
│  └─ [17 more]
│
├─ Seafood Specialists (15):
│
├─ Fine Dining (20+):
│
└─ Modern Cafes (10+):

Data Points per Restaurant:
  ✓ Name, cuisine types, specialties
  ✓ Price range (avg per person in INR)
  ✓ Veg/vegan options availability
  ✓ Allergen information (nuts, dairy, gluten)
  ✓ Operating hours (with breaks)
  ✓ Precise coordinates & area
  ✓ Popular dishes (with prices)
  ✓ Ratings (Google, Zomato, local)
  ✓ Ambiance (casual, formal, romantic)
  ✓ Reservation requirements
  ✓ Contact info (phone, website)
  ✓ Images (3-5 of food & ambiance)

HOTELS (Target: 40-50)
├─ 5-Star Luxury (8):
│  ├─ Taj Mahal Palace
│  ├─ ITC Grand Central
│  └─ [6 more]
│
├─ 4-Star Business (10):
│  ├─ Radisson Blu
│  └─ [9 more]
│
├─ 3-Star Mid-Range (15):
│  ├─ FabHotels
│  └─ [14 more]
│
├─ Budget Hotels (10):
│  ├─ OYO Rooms
│  └─ [9 more]
│
└─ Heritage/Unique Stays (7):

Data Points per Hotel:
  ✓ Name, stars, district/area
  ✓ Price ranges (economy, standard, premium)
  ✓ Amenities list (WiFi, AC, breakfast, gym, pool)
  ✓ Accessibility features
  ✓ Check-in/check-out times
  ✓ Cancellation policy
  ✓ Coordinates & nearest attractions
  ✓ Contact info (phone, email, website)
  ✓ 5-8 quality images
  ✓ Unique selling points

CULTURAL INFORMATION (Target: 15+)
├─ History of Mumbai (2 entries):
│  ├─ Colonial era & British rule
│  └─ Post-independence development
│
├─ Festivals & Celebrations (5):
│  ├─ Ganesh Chaturthi (dates, traditions)
│  ├─ Navratri celebrations
│  ├─ Durga Puja
│  ├─ Holi
│  └─ Christmas in Mumbai
│
├─ Local Customs & Etiquette (3):
│  ├─ Temple visiting etiquette
│  ├─ Diwali customs
│  └─ Respectful behavior in public
│
├─ Art & Architecture (3):
│  ├─ Victorian Gothic architecture
│  ├─ Art Deco buildings
│  └─ Modern infrastructure
│
└─ Local Lifestyle (2):
   ├─ Mumbai's fast pace & culture
   └─ Work-life balance insights

Data Points per Cultural Entry:
  ✓ Title, category, detailed content (300+ words)
  ✓ Historical background & significance
  ✓ Associated monuments/locations
  ✓ Festival dates (if applicable)
  ✓ Do's (5-10 items)
  ✓ Don'ts (5-10 items)
  ✓ Impact on travel experience
  ✓ References & sources

SAFETY GUIDELINES (Target: 10+)
├─ Women's Safety (2):
│  ├─ Safe areas & unsafe areas by time
│  └─ Gender-specific safety tips
│
├─ Traffic Safety (2):
│  ├─ Mumbai traffic rules
│  └─ Safe crossing & commuting
│
├─ Theft Prevention (2):
│  ├─ Theft hotspots & prevention
│  └─ Valuables protection
│
├─ Health & Emergency (2):
│  ├─ Medical facilities & contact
│  └─ Disease prevention (monsoon, etc.)
│
├─ Area-Specific Safety (2):
│  └─ Neighborhood breakdown

Data Points per Safety Entry:
  ✓ Category, severity level
  ✓ Detailed content (practical advice)
  ✓ Relevant traveler types
  ✓ Location-specific info (if applicable)
  ✓ Prevention tips (5-10 items)
  ✓ Emergency contacts (police, ambulance)
  ✓ Latest updates (date)
```

#### AHMEDABAD - Data Requirements

```
ATTRACTIONS (Target: 40-60)
├─ Historical Sites (12):
│  ├─ Ahmedabad Fort
│  ├─ Jama Mosque
│  ├─ Sabarmati Ghats
│  ├─ Calico Museum
│  ├─ Hutheesing Temple
│  └─ [7 more]
│
├─ Religious Sites (10):
│  ├─ ISCON Temple
│  ├─ Swaminarayan Temple
│  ├─ Jain temples
│  └─ [7 more]
│
├─ Museums (8):
│  ├─ Textile Museum
│  ├─ Auto Museum
│  └─ [6 more]
│
├─ Markets (8):
│  ├─ Delhi Bazaar
│  ├─ Bhagirath Market
│  └─ [6 more]
│
└─ Modern Attractions (6):
   └─ Include contemporary spaces

RESTAURANTS (Target: 60+)
├─ Gujarati Cuisine (20):
│  ├─ Dhokla houses
│  ├─ Fafda/Jalebi places
│  ├─ Thepla houses
│  └─ [17 more]
│
├─ Street Food (15):
│
├─ North Indian (10):
│
├─ Modern/International (10):
│
└─ Specialty Restaurants (5):

HOTELS (Target: 30-40)
├─ Heritage Hotels (5):
├─ Business Hotels (8):
├─ Mid-Range (12):
└─ Budget Hotels (8-15):

CULTURAL INFO (Target: 10-12)
├─ Textile heritage (2)
├─ Gandhi connection (2)
├─ Festival calendar (2) - Navratri, Kite Festival
├─ Local customs (2)
└─ Art & craft traditions (2-4)

SAFETY (Target: 6-8)
├─ General safety (1)
├─ Women travelers (1)
├─ Market navigation (1)
├─ Health alerts (1)
└─ Emergency info (1-3)
```

#### GWALIOR - Data Requirements

```
ATTRACTIONS (Target: 35-50)
├─ Gwalior Fort (major)
├─ Jai Vilas Palace
├─ Tansen Tomb
├─ Man Singh Palace
├─ Suraj Kund Lake
├─ Gurudwara
├─ Art galleries
└─ [+ More local sites]

RESTAURANTS (Target: 30-40)
├─ Poha specialty
├─ Central Indian cuisine
├─ Street food
└─ Local eateries

HOTELS (Target: 20-25)
├─ Mid-range hotels
├─ Budget accommodation
└─ Heritage stays

CULTURAL INFO (Target: 8-10)
├─ Fort history & significance
├─ Music heritage (Tansen)
├─ Local martial traditions
└─ Festival calendar

SAFETY (Target: 5-6)
├─ General information
├─ Traffic rules
└─ Emergency contacts
```

### 4.2 Data Collection Sources & Methods

#### Method 1: API Integrations

```python
# Google Maps API
- Attractions with high reviews/ratings
- Ratings, photos, opening hours
- Directions & distance calculations
- Google Workspace integration

# Zomato API
- Comprehensive restaurant database
- Photos, menus, reviews
- Real-time availability
- Ratings across platforms

# OpenWeatherMap API
- Weather forecasts
- Historical weather patterns
- Seasonal information

# OpenStreetMap API
- Additional venue information
- Map data for navigation
```

#### Method 2: Web Scraping

```python
# Tools: Selenium, BeautifulSoup

Targets:
- TripAdvisor (reviews, ratings, top attractions)
- OYO/Booking.com (hotel data, pricing)
- Zomato website (if API insufficient)
- Local tourism websites
- Travel blogs (for hidden gems)
```

#### Method 3: Manual Curation

```
Spreadsheet Collection:

1. Create Google Sheets with templates:
   - Attractions Template (standard fields)
   - Restaurants Template
   - Hotels Template
   - Cultural Info Template
   - Safety Guidelines Template

2. Collaborative editing:
   - Share with local experts/travelers
   - Validate information
   - Add personal insights

3. Export to JSON/CSV
   - Convert sheets to structured data
   - Validate against schema
   - Upload to database
```

#### Method 4: Community & Expert Input

```
Sources:
- Reddit threads (r/India, city subreddits)
- Local travel guides (written by residents)
- Travel blogs (verified sources)
- Tourist board recommendations
- Hotel/restaurant direct contact
- Local NGOs & cultural centers
```

### 4.3 Data Collection Timeline

```
WEEK 1: SETUP & ATTRACTIONS
Monday-Tuesday:
  ☐ Set up Google Maps API credentials
  ☐ Set up Zomato API credentials
  ☐ Set up OpenWeatherMap API
  ☐ Create Google Sheets templates
  ☐ Set up local development database

Wednesday-Friday:
  ☐ Scrape/Collect 50-70 attractions per city
  ☐ Validate & deduplicate
  ☐ Enrich with descriptions & history
  ☐ Extract all required data points
  ☐ Quality check

WEEK 2: HOTELS & BASIC RESTAURANTS
Monday-Wednesday:
  ☐ Collect 30-50 hotels per city
  ☐ Extract pricing (off/peak seasons)
  ☐ Add amenities & accessibility info
  ☐ Quality validation

Thursday-Friday:
  ☐ Collect 60-100 restaurants per city
  ☐ Validate specialties & pricing
  ☐ Flag vegetarian/dietary options
  ☐ Add ratings from multiple sources

WEEK 3: STREET FOOD & CULTURAL DATA
Monday-Wednesday:
  ☐ Add street food locations & tips
  ☐ Collect cultural information (history, festivals)
  ☐ Gather safety guidelines
  ☐ Add local customs & etiquette

Thursday-Friday:
  ☐ Fill in festival calendars
  ☐ Complete cultural do's & don'ts
  ☐ Add emergency contacts
  ☐ Validation & cleanup

WEEK 4: TESTING & REFINEMENT
Monday-Wednesday:
  ☐ Test all data APIs
  ☐ Check coordinate accuracy
  ☐ Validate phone numbers & websites
  ☐ Cross-check review platforms

Thursday-Friday:
  ☐ Remove duplicates
  ☐ Final quality validation
  ☐ Fix missing data
  ☐ Database population complete
```

### 4.4 Data Gathering Checklist

```
PRE-COLLECTION:
☐ API Credentials Setup
  ☐ Google Maps API key
  ☐ Zomato API credentials
  ☐ OpenWeatherMap API key
  ☐ Test all APIs locally

☐ Database Setup
  ☐ MongoDB instances for each city
  ☐ PostgreSQL schema created
  ☐ Backup strategy defined

☐ Tools Installation
  ☐ Selenium WebDriver
  ☐ BeautifulSoup4
  ☐ Requests library
  ☐ Pandas
  ☐ Python data validation library

☐ Team Resources
  ☐ Local experts/advisors assigned
  ☐ Data validation checklist created
  ☐ Communication channel set up

COLLECTION PHASE:
☐ Mumbai Data Collection
  ☐ 50-70 attractions collected
  ☐ 100+ restaurants collected
  ☐ 40-50 hotels collected
  ☐ 15+ cultural info entries
  ☐ 10+ safety guidelines

☐ Ahmedabad Data Collection
  ☐ 40-60 attractions collected
  ☐ 60+ restaurants collected
  ☐ 30-40 hotels collected
  ☐ 10-12 cultural info entries
  ☐ 6-8 safety guidelines

☐ Gwalior Data Collection
  ☐ 35-50 attractions collected
  ☐ 30-40 restaurants collected
  ☐ 20-25 hotels collected
  ☐ 8-10 cultural info entries
  ☐ 5-6 safety guidelines

VALIDATION & CLEANUP:
☐ Data Quality Checks
  ☐ All required fields present
  ☐ No invalid coordinates
  ☐ Phone numbers formatted correctly
  ☐ URLs valid & accessible
  ☐ Ratings within valid ranges
  ☐ Prices realistic
  ☐ Opening hours logical

☐ Deduplication
  ☐ Remove duplicate attractions
  ☐ Merge similar restaurants
  ☐ Check for alternate names

☐ Final Validation
  ☐ All cities at target counts
  ☐ All data points populated
  ☐ Random sampling verified
  ☐ Ready for database import
```

---

## PYTHON BACKEND ARCHITECTURE

### 5.1 Project Structure

```
local_buddy/
│
├── core/
│   ├── __init__.py
│   ├── agent.py                    # Base agent class
│   ├── orchestrator.py             # Main orchestrator agent
│   ├── context_manager.py          # User session & context
│   ├── intent_classifier.py        # Intent detection
│   └── response_formatter.py       # Format responses
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py               # Base agent class
│   ├── travel_agent.py             # Travel planning
│   ├── food_agent.py               # Food recommendations
│   ├── culture_agent.py            # Cultural information
│   ├── safety_agent.py             # Safety guidelines
│   └── language_agent.py           # Translations
│
├── data/
│   ├── __init__.py
│   ├── database.py                 # DB connection management
│   ├── models.py                   # SQLAlchemy models
│   ├── repository.py               # Data access layer
│   └── seeders/
│       ├── __init__.py
│       ├── attractions.py
│       ├── restaurants.py
│       ├── hotels.py
│       ├── cultural_info.py
│       └── safety_guidelines.py
│
├── realtime/
│   ├── __init__.py
│   ├── weather_service.py          # Weather API integration
│   ├── traffic_service.py          # Traffic/transit data
│   ├── event_service.py            # Events & festivals
│   ├── restaurant_service.py       # Live restaurant data
│   ├── cache.py                    # Redis caching
│   └── job_scheduler.py            # Background jobs
│
├── api/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app initialization
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py                 # Chat endpoint
│   │   ├── cities.py               # City information
│   │   └── search.py               # Search endpoints
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py                 # Authentication
│       ├── logging.py              # Request logging
│       └── cors.py                 # CORS handling
│
├── utils/
│   ├── __init__.py
│   ├── logger.py                   # Logging setup
│   ├── validators.py               # Data validation
│   ├── formatters.py               # Response formatting
│   ├── constants.py                # App constants
│   └── exceptions.py               # Custom exceptions
│
├── config/
│   ├── __init__.py
│   ├── settings.py                 # Configuration management
│   ├── cities_config.py            # City-specific configs
│   └── prompts/
│       ├── orchestrator_prompt.py
│       ├── travel_agent_prompt.py
│       ├── food_agent_prompt.py
│       ├── culture_agent_prompt.py
│       ├── safety_agent_prompt.py
│       └── language_agent_prompt.py
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_api.py
│   ├── test_data.py
│   └── test_integration.py
│
├── requirements.txt
├── docker-compose.yml              # Docker setup
├── .env.example                    # Environment template
└── README.md
```

### 5.2 Technology Stack

```
# requirements.txt

# Web Framework
fastapi==0.104.0                # Modern web framework
uvicorn==0.24.0                 # ASGI server
pydantic==2.4.0                 # Data validation
python-multipart==0.0.6         # Form data handling

# AI & API Integration
anthropic==0.7.0                # Claude API access
requests==2.31.0                # HTTP client
aiohttp==3.9.0                  # Async HTTP

# Database
sqlalchemy==2.0.0               # ORM for relational DB
pymongo==4.6.0                  # MongoDB driver
alembic==1.12.0                 # Database migrations
psycopg2-binary==2.9.0          # PostgreSQL adapter

# Caching & Real-Time
redis==5.0.0                    # Redis client
celery==5.3.0                   # Task queue
apscheduler==3.10.0             # Job scheduler

# Data Processing
pandas==2.1.0                   # Data manipulation
numpy==1.24.0                   # Numerical operations
python-dotenv==1.0.0            # Environment variables

# Web Scraping
selenium==4.14.0                # Browser automation
beautifulsoup4==4.12.0          # HTML parsing
lxml==4.9.0                     # XML parsing
requests-html==0.10.0           # HTML parsing for requests

# NLP & Language
nltk==3.8.0                     # NLP toolkit
textblob==0.17.0                # Sentiment analysis
geopy==2.3.0                    # Geocoding

# Testing
pytest==7.4.0                   # Testing framework
pytest-asyncio==0.21.0          # Async test support
pytest-cov==4.1.0               # Coverage reporting

# Monitoring & Logging
python-json-logger==2.0.0       # JSON logging
sentry-sdk==1.38.0              # Error tracking
pydantic-settings==2.0.0        # Settings management

# Utilities
pyyaml==6.0.0                   # YAML parsing
python-dateutil==2.8.0          # Date utilities
pytz==2023.3                    # Timezone support
```

### 5.3 Core Application Flow

```python
# main.py - FastAPI Application Structure

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Initialize logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Local Buddy API",
    description="AI Travel Companion for Indian Cities",
    version="1.0.0"
)

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.routes import chat, cities, search

app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(cities.router, prefix="/api/v1/cities", tags=["Cities"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup"""
    logger.info("Starting Local Buddy API...")
    # Initialize database connections
    # Initialize real-time data services
    # Start background jobs
    logger.info("All services initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on app shutdown"""
    logger.info("Shutting down Local Buddy API...")
    # Close database connections
    # Stop background jobs

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Local Buddy API"}
```

### 5.4 API Endpoints

```
Chat & Interaction:
POST /api/v1/chat/message
  - Send user message
  - Get AI response from orchestrator

City Information:
GET /api/v1/cities/list
  - Get all available cities

GET /api/v1/cities/{city_id}/overview
  - Get city overview & basic info

GET /api/v1/cities/{city_id}/attractions
  - Get all attractions in city
  - Query params: category, budget, duration

GET /api/v1/cities/{city_id}/restaurants
  - Get restaurants
  - Query params: cuisine, price, vegetarian

GET /api/v1/cities/{city_id}/hotels
  - Get hotels
  - Query params: price_range, amenities

Search:
GET /api/v1/search/attractions
  - Search across all cities
  - Query params: query, city, distance

GET /api/v1/search/restaurants
  - Search restaurants
  - Query params: cuisine, price, location

Real-Time Data:
GET /api/v1/realtime/weather/{city_id}
  - Get current weather

GET /api/v1/realtime/events/{city_id}
  - Get current events & festivals

GET /api/v1/realtime/traffic/{city_id}
  - Get traffic conditions
```

### 5.5 Agent Architecture

```python
# core/agent.py - Base Agent Class

from abc import ABC, abstractmethod
from anthropic import Anthropic

class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, city_id: str, context: dict):
        self.city_id = city_id
        self.context = context
        self.client = Anthropic()
        self.model = "claude-opus-4-5"

    @abstractmethod
    def create_system_prompt(self) -> str:
        """Create agent-specific system prompt"""
        pass

    @abstractmethod
    def process_query(self, query: str) -> str:
        """Process user query and return response"""
        pass

    def call_claude(self, system_prompt: str, user_message: str) -> str:
        """Call Claude API with system prompt and message"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return message.content[0].text
```

---

## IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-2)

```
WEEK 1:
  ☐ Set up project repository & structure
  ☐ Configure Python environment & dependencies
  ☐ Set up MongoDB/PostgreSQL databases
  ☐ Initialize FastAPI application
  ☐ Set up API credentials (Google Maps, Zomato, etc.)

WEEK 2:
  ☐ Implement database models (SQLAlchemy)
  ☐ Create data repository layer
  ☐ Build basic API routes
  ☐ Set up logging & monitoring
  ☐ Create base agent class
```

### Phase 2: Data Collection (Weeks 3-6)

```
WEEK 3-4: Data Gathering
  ☐ Implement data scraping scripts
  ☐ Collect attractions (all cities)
  ☐ Collect restaurants (all cities)
  ☐ Collect hotels (all cities)
  ☐ Data validation & deduplication

WEEK 5-6: Data Enrichment
  ☐ Manually curate cultural information
  ☐ Add safety guidelines
  ☐ Populate database with clean data
  ☐ Set up real-time data ingestion
```

### Phase 3: Agent Implementation (Weeks 7-10)

```
WEEK 7: Orchestrator & Intent
  ☐ Implement Orchestrator Agent
  ☐ Build intent classifier
  ☐ Set up context manager
  ☐ Test basic routing

WEEK 8: Travel Agent
  ☐ Implement Travel Planning Agent
  ☐ Create itinerary generation logic
  ☐ Add hotel/attraction filtering
  ☐ Test with sample queries

WEEK 9: Food & Culture Agents
  ☐ Implement Food Agent
  ☐ Implement Culture Agent
  ☐ Add dietary preference handling
  ☐ Add cultural information retrieval

WEEK 10: Safety & Language Agents
  ☐ Implement Safety Agent
  ☐ Implement Language Agent
  ☐ Add real-time safety updates
  ☐ Add translation functionality
```

### Phase 4: Real-Time Integration (Weeks 11-12)

```
WEEK 11: Real-Time Services
  ☐ Integrate Weather API
  ☐ Integrate Traffic/Transit API
  ☐ Set up events data service
  ☐ Cache layer with Redis

WEEK 12: Background Jobs
  ☐ Set up Celery task queue
  ☐ Configure APScheduler
  ☐ Implement job scheduling
  ☐ Test all real-time services
```

### Phase 5: Testing & Deployment (Weeks 13-14)

```
WEEK 13: Testing
  ☐ Unit tests for agents
  ☐ Integration tests for API
  ☐ Data validation tests
  ☐ Performance testing
  ☐ User acceptance testing

WEEK 14: Deployment
  ☐ Set up Docker containerization
  ☐ Configure production database
  ☐ Set up deployment pipeline
  ☐ Deploy to production
  ☐ Monitor & optimize
```

---

## AGENT PROMPTS TEMPLATE

### Orchestrator Agent Prompt

```
You are the Local Buddy Orchestrator - a friendly and knowledgeable travel companion AI.

Your role is to:
1. Understand the traveler's needs, preferences, and context
2. Route requests to appropriate specialized agents
3. Synthesize responses from multiple agents
4. Provide comprehensive, personalized travel advice

Key Principles:
- Be helpful, friendly, and encouraging
- Remember user context from previous interactions
- Consider diverse traveler needs (accessibility, dietary, gender safety, etc.)
- Provide authentic, respectful cultural guidance
- Prioritize traveler safety in all recommendations
- Cross-reference information across agents

When processing requests:
1. Analyze the user's intent and context
2. Identify which agents should be consulted
3. Request information from relevant agents
4. Synthesize into a coherent, personalized response
5. Add relevant safety, cultural, and practical context

Guidelines:
- Always consider user safety as primary concern
- Respect local culture and traditions
- Be honest about limitations/risks
- Provide practical, actionable advice
- Maintain conversational, friendly tone
```

### Travel Agent Prompt

```
You are the Travel Planning Expert for [CITY_NAME].

Your expertise includes:
- Best attractions and their historical significance
- Optimal route planning and time sequencing
- Hotel recommendations across budget ranges
- Transportation options and navigation
- Time management for activities
- Seasonal weather patterns and best visit times
- Local events and festivals

You have access to:
- Complete attraction database
- Hotel inventory with pricing
- Real-time traffic and transit information
- Weather forecasts and patterns

Guidelines:
- Create time-optimized itineraries
- Consider physical accessibility
- Suggest authentic experiences
- Balance popular and lesser-known attractions
- Provide accurate timing and cost estimates
- Adapt recommendations based on traveler profile
- Consider weather and seasonal factors
- Suggest best transportation methods
```

...and so on for each agent type.

---

## NEXT IMMEDIATE STEPS

You have two paths forward:

**PATH A: Data Collection First** (Recommended)
1. Set up API credentials and tools
2. Create data collection scripts
3. Run data gathering for 3 cities
4. Validate and populate database
5. Then build agents with real data

**PATH B: Backend Development First**
1. Set up FastAPI project
2. Design and implement database schemas
3. Build agent infrastructure
4. Create API endpoints
5. Integrate data as it becomes available

---

## QUICK START COMMANDS

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run data collection
python -m data.seeders.collect_attractions
python -m data.seeders.collect_restaurants
python -m data.seeders.collect_hotels

# Start API
uvicorn api.main:app --reload

# Run tests
pytest tests/ -v

# Docker
docker-compose up
```

---

## Key Files to Create First

1. `requirements.txt` - Dependencies
2. `config/settings.py` - Configuration
3. `data/models.py` - Database models
4. `core/orchestrator.py` - Main agent
5. `api/main.py` - FastAPI app
6. `.env.example` - Environment setup

---

**Status**: Architecture & Planning Complete ✓
**Next**: Ready for implementation
**Questions?** See sections above or start with chosen path.


# LOCAL BUDDY - KNOWLEDGE GRAPH ARCHITECTURE & DATA FLOW

**Document**: Complete Technical Vision
**Version**: 2.0 - Graph-Centric Design
**Date**: 2026-06-06

---

## TABLE OF CONTENTS

1. [User Personas & Real-World Needs](#user-personas--real-world-needs)
2. [Core Vision](#core-vision)
3. [Knowledge Graph Schema](#knowledge-graph-schema)
4. [Data Layer Architecture](#data-layer-architecture)
5. [Data Flow & Processing](#data-flow--processing)
6. [Multi-City Scaling Strategy](#multi-city-scaling-strategy)
7. [User Model & Personalization](#user-model--personalization)
8. [Real-Time Integration](#real-time-integration)
9. [Technical Implementation](#technical-implementation)
10. [Data Quality & Evolution](#data-quality--evolution)
11. [MVP Scope & Build Plan](#mvp-scope--build-plan)

---

## USER PERSONAS & REAL-WORLD NEEDS

### Why This Matters
Local Buddy isn't built for tourists alone — it's built for **life changers**: people whose entire daily context is shifting. This section maps *actual needs* to graph structures.

### Persona 1: Relocating Professional (Priya, 28)
```
Background:
├─ Senior dev at Bangalore startup
├─ Got job offer at Ahmedabad fintech firm
├─ Moving in 2 weeks
├─ Budget: ₹50k/month rent comfortable
└─ Mission: Integrate asap, maintain social life

Immediate Problems:
├─ How bad is Ahmedabad traffic? (vs Bangalore metro)
├─ Will my salary go as far for rent?
├─ Work culture different? Will I fit?
├─ Where do young professionals hang out?
├─ How to get Indian SIM + apartment quickly?
├─ What neighborhoods are like Indiranagar (where I lived)?
└─ Dating scene — is it progressive?

Graph Needs:
├─ Area Vibe Matching
│  └─ Indiranagar (Bangalore) --SIMILAR_VIBE--> [Ahmedabad areas]
│     {techie: 0.8, progressive: 0.7, trendy_cafes: 0.9}
│
├─ Work Culture Norms
│  ├─ Delhi norm: "Strong hierarchy"
│  └─ --CONFLICTS_WITH--> Ahmedabad norm: "Flat structure in startups"
│
├─ Cost of Living Index
│  ├─ 1BHK Indiranagar: ₹35k
│  ├─ 1BHK Naranpura: ₹22k
│  └─ "Purchasing power parity"
│
├─ Lifestyle Compatibility
│  ├─ Nightlife options (bars, clubs)
│  ├─ Dating/social communities
│  └─ Expat/young professional networks
│
└─ Quick Setup Checklist
   ├─ Apartment hunting in safe areas
   ├─ Phone + utilities setup
   ├─ Bank account opening
   ├─ ID proof requirements (Aadhaar vs passport)
   └─ First week survival kit
```

### Persona 2: Traveling Backpacker (Ravi, 24)
```
Background:
├─ College student, 2-week vacation
├─ First time in Ahmedabad
├─ Budget: ₹1500/day, backpacker hostel
├─ Mission: See culture, eat well, stay safe

Immediate Problems:
├─ What's unique about Ahmedabad (not Mumbai again)?
├─ Best street food without getting sick?
├─ Safe areas to walk at night (solo male)?
├─ How to negotiate auto/taxi prices?
├─ Traditional vs modern areas to see?
├─ Which temples/markets are essential?
└─ How to meet locals/travelers?

Graph Needs:
├─ Quintessential Experiences
│  ├─ Jama Mosque (morning prayer)
│  ├─ Sabarmati Ashram (Gandhi history)
│  ├─ Street food crawl (Navratan)
│  └─ Calico Museum (textile history)
│
├─ Street Smarts
│  ├─ Bargaining norms in markets (critical!)
│  ├─ Rickshaw prices (prepay or meter?)
│  ├─ Safe neighborhoods 24/7 vs after dark
│  └─ Which restaurants guarantee good hygiene
│
├─ Language Phrases (Hindi → Gujarati)
│  ├─ "Ek chai dilao" vs Gujarati equivalent
│  ├─ "Kitne mein?" (price negotiation)
│  └─ Emergency phrases
│
├─ Budget-Friendly Routes
│  ├─ Free/cheap attractions
│  ├─ Best thali spots (<₹150)
│  └─ Hostel-recommended routes (crowded ok)
│
└─ Safety by Time of Day
   ├─ 8pm: Chaotic but safe
   ├─ 10pm: Risky solo
   ├─ 2am: Only in cabs
   └─ Female traveler addendum
```

### Persona 3: Family Relocating (Sharma family)
```
Background:
├─ Dad transferred to Ahmedabad office (ISRO)
├─ Family of 4: Wife, kids (8, 12)
├─ Budget: ₹80k/month, family flat needed
├─ Mission: Good schools, safe, normal life

Immediate Problems:
├─ Schools ranked by quality/fees?
├─ Healthcare hospitals for emergencies?
├─ Safe neighborhoods with other families?
├─ Kids' extracurriculars (sports, tutoring)?
├─ Wife community: schools, kitty groups?
├─ How progressive is Ahmedabad (clothes, social)?
└─ Do kids' friends speak Hindi/all Hindi medium?

Graph Needs:
├─ School Finder
│  ├─ Ranking: CISCE, CBSE, Gujarati medium
│  ├─ Fees range: ₹1-5L/year
│  ├─ Neighborhood: Near which residential areas?
│  └─ Reviews from expat parents
│
├─ Family-Safe Areas
│  ├─ Satellite, Mohan Nagar, Rajsansi
│  ├─ Safety rating for families
│  ├─ Schools within 5km
│  └─ Hospitals, parks nearby
│
├─ Healthcare Facilities
│  ├─ Top hospitals (Shardaben, Raghuvanshi)
│  ├─ English-speaking doctors
│  ├─ Emergency protocols
│  └─ Pediatricians
│
├─ Social Integration
│  ├─ Expat parent communities
│  ├─ Women's circles/kitty groups
│  ├─ Cultural do's & don'ts
│  └─ Religious diversity acceptance
│
└─ Family Norms vs Bangalore Norms
   ├─ Conservative dress code?
   ├─ Mixed-gender socializing OK?
   ├─ Alcohol acceptance?
   ├─ Dating teenagers OK?
   └─ Dietary restrictions (vegetarian cities)
```

### Persona 4: Student Moving (Aisha, 21)
```
Background:
├─ Masters admission: AIMS, Ahmedabad
├─ First time alone in new city
├─ Budget: ₹25k/month (hostel + food)
├─ Mission: Academics + social life + independence

Immediate Problems:
├─ Hostel quality & safety for women?
├─ Walk-safe university area?
├─ Affordable food near campus?
├─ Women's safety hours (can I be out at midnight)?
├─ LGBT+ friendly community?
├─ Online friends vs making local friends?
└─ Part-time job opportunities?

Graph Needs:
├─ Campus Surrounding Context
│  ├─ AIMS location in Ahmedabad
│  ├─ Safe routes from hostel → campus
│  ├─ 24-hour food availability
│  └─ Study spaces (libraries, cafes)
│
├─ Women-Specific Safety
│  ├─ Areas NEVER go solo after dark
│  ├─ Trusted auto stands
│  ├─ Police contacts + response time
│  └─ Women's support groups on campus
│
├─ Social Community
│  ├─ Student groups & clubs
│  ├─ LGBT+ friendly spaces
│  ├─ Cultural communities (if not local)
│  └─ Networking events
│
├─ Budget Living
│  ├─ Hostel reviews (price, vibe)
│  ├─ Mess vs self-cooking
│  ├─ Part-time job locations
│  └─ Scholarship/financial aid info
│
└─ Norms for Young Women
   ├─ Dating openly OK?
   ├─ Solo travel norm?
   ├─ Drinking/nightlife (religious context)?
   └─ Relationship with parents (tell them everything?)
```

---

## What These Personas Tell Us About Features to Add

### 1. Cost of Living Comparisons (NEW NODE TYPE)
```cypher
CREATE (coli:CostOfLiving {
  id: "coli_ahmedabad_1bhk_2024",
  city: "ahmedabad",
  category: "accommodation",
  item: "1BHK apartment rent",
  price_range: {min: 15000, max: 35000, avg: 22000},
  neighborhood_breakdown: {
    "Satellite": {price: 28000, vibe: "modern"},
    "Naranpura": {price: 20000, vibe: "traditional"},
    "Bodakdev": {price: 25000, vibe: "mixed"}
  },
  compared_to: {
    city: "bangalore",
    avg_price: 35000,
    purchasing_power_ratio: 0.65
  }
})
```

### 2. Area Vibe Similarity Index (EDGE TYPE)
```cypher
// Instead of manually matching areas, compute similarity
Indiranagar --SIMILAR_VIBE_TO--> Naranpura
[similarity_score: 0.72,
 shared_traits: ["tech_professionals", "cafes", "progressive"],
 differences: ["cost_30%_cheaper", "less_trendy"]]
```

### 3. School Finder Knowledge (NEW NODE TYPE)
```cypher
CREATE (school:School {
  id: "school_ahmedabad_cis",
  city: "ahmedabad",
  name: "Ahmedabad International School",
  type: "CISCE",
  annual_fees: 280000,
  grades: [1, 2, 3, ..., 12],
  safety_rating: 9.2,
  parent_reviews: 4.7,
  location_coordinates: {lat: 23.1815, lng: 72.6225},
  nearest_residential_area: ["Satellite", "Vesu"],
  distance_from_city_center_km: 8
})
```

### 4. Safety Hours & Gender Context (EDGE TYPE)
```cypher
Area --SAFE_FOR_GENDER--> {
  female: {
    morning_to_9pm: "very_safe",
    9pm_to_midnight: "avoid_solo",
    midnight_onward: "dangerous"
  },
  male: {
    anytime: "safe",
    late_night: "normal"
  },
  lgbtq: {
    public_affection: "risky",
    LGBT_spaces: "safe"
  }
}
```

### 5. Quick Setup Checklist (NEW NODE TYPE)
```cypher
CREATE (setup:QuickSetup {
  id: "setup_new_arrivals_ahmedabad",
  city: "ahmedabad",
  target_user: ["relocating_professional", "student"],
  timeline: "first_2_weeks",
  tasks: [
    {order: 1, task: "Find accommodation", time_hours: 24, links: [school_node, area_node]},
    {order: 2, task: "Phone SIM setup", time_hours: 2, location: "Any telecom store"},
    {order: 3, task: "Bank account", time_hours: 4, documents: ["Aadhaar", "Address proof"]},
    {order: 4, task: "Understand transport", time_hours: 8, resource: "Metro vs auto guide"},
    {order: 5, task: "First social meetup", time_hours: 4, link: "Community groups node"}
  ]
})
```

### 6. Work Culture Comparisons (EDGE TYPE)
```cypher
(:Norm {title: "Hierarchy", city: "Delhi"})
  --DIFFERS_FROM-->
  (:Norm {title: "Flat structure", city: "Ahmedabad_startups"})
  [conflict_level: "high", embarrassment_risk: "medium",
   context: "In startup interviews and daily work"]
```

---

## CORE VISION

### The Three-Pillar System

Local Buddy is fundamentally built on three interconnected systems:

```
┌──────────────────────────────────────────────────────────────┐
│                         LOCAL BUDDY                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐    ┌──────────────────┐   ┌──────────┐ │
│  │ Knowledge Graph │◄──►│ User Model       │◄─►│ Agent    │ │
│  │ (Neo4j)         │    │ (PostgreSQL)     │   │ Engine   │ │
│  │                 │    │                  │   │ (Claude) │ │
│  │ What to know    │    │ Who they are     │   │ What to  │ │
│  │ about cities    │    │ + what they know │   │ show next│ │
│  └─────────────────┘    └──────────────────┘   └──────────┘ │
│         ▲                        ▲                    ▲       │
│         │                        │                    │       │
│         └────────────────────────┴────────────────────┘       │
│                  Real-time Data Sync Layer                    │
│              (Weather, Traffic, Events, Safety)              │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Frontend (Mobile/Web)
         │
         ▼
  API Gateway (FastAPI)
         │
         ├──► Orchestrator Agent
         │    │
         │    ├──► Graph DB Queries
         │    ├──► User Context Fetch
         │    └──► Real-time Data
         │
         └──► Response Synthesis
```

### Why This Design?

**Knowledge Graph (Neo4j)** = Single Source of Truth for City Knowledge
- Stores structured relationships between places, norms, culture, language
- Enables efficient traversal (what's connected to what)
- Scales to thousands of nodes per city
- Handles the **conflict edges** (taboo vs normal across cities)

**User Model (PostgreSQL)** = Personalization State
- Tracks what each user has learned
- Records retention scores and engagement
- Stores preferences and context
- Enables spaced repetition and adaptive learning

**Agentic Engine (Claude API)** = Intelligent Routing
- Understands natural language queries
- Decides which graph nodes are relevant
- Synthesizes multi-source responses
- Learns from user interactions

---

## KNOWLEDGE GRAPH SCHEMA

### 1. Node Types & Properties

#### City Node
```cypher
CREATE (city:City {
  id: "mumbai",
  name: "Mumbai",
  state: "Maharashtra",
  country: "India",
  population: 20411000,
  primary_language: "Marathi",
  secondary_languages: ["Hindi", "English"],
  timezone: "IST",
  currency: "INR",
  climate_type: "tropical_monsoon",
  urban_density: "high",
  culture_vibe: "cosmopolitan_fast_paced",
  cost_of_living: 85,
  safety_index: 6.5,
  infrastructure_score: 8.2,
  established_year: 1661,
  history_era: "colonial_modern",
  gini_coefficient: 0.55,
  description: "Financial capital of India..."
})
```

#### Area Node
```cypher
CREATE (area:Area {
  id: "bandra_mumbai",
  name: "Bandra",
  city: "mumbai",
  locality_type: "suburban_trendy",
  coordinates: {lat: 19.0596, lng: 72.8295},
  population: 250000,
  average_rent_1bhk: 45000,
  demographics: {
    median_age: 32,
    employment_sectors: ["IT", "Finance", "Creative"],
    collar_type: "white"
  },
  lifestyle_tags: ["artsy", "expat_friendly", "nightlife", "cafes"],
  safety_level: "high",
  public_transport: 9,
  walkability: 8,
  cultural_vibe: "young_professional",
  area_reputation: "trendy_expensive",
  notable_for: ["Leopold Cafe", "Bandra Fort", "Street Art", "Restaurants"]
})
```

#### Place Node
```cypher
CREATE (place:Place {
  id: "taj_gateway_mumbai",
  name: "Gateway of India",
  city: "mumbai",
  area: "colaba",
  type: "monument",
  category: "historical_iconic",
  significance: "national_symbol",
  coordinates: {lat: 18.9220, lng: 72.8347},
  visiting_hours: {
    open: "09:00",
    close: "23:00",
    duration_hours: 1.5
  },
  entry_fee: {local: 0, foreign: 600, child: 0},
  best_visiting_time: {season: "nov_to_feb", time_of_day: "sunset"},
  crowd_level: {
    morning: "medium",
    afternoon: "high",
    evening: "high",
    night: "low"
  },
  accessibility: {
    wheelchair: true,
    parking: true,
    washrooms: true,
    disabled_friendly: true
  },
  photography: {allowed: true, tripod: false},
  distance_from_center_km: 0,
  description: "Iconic 26m tall stone archway...",
  historical_significance: "British colonial era gateway...",
  must_visit_reason: true,
  images: ["url1", "url2", "url3"]
})
```

#### Norm Node (The Critical One)
```cypher
CREATE (norm:Norm {
  id: "bargaining_market_mumbai",
  title: "Bargaining in Markets",
  city: "mumbai",
  category: "commerce",
  description: "In Mumbai street markets and souvenir shops...",

  // Feature vector for conflict detection
  formality_level: 0.7,
  collectivist_score: 0.4,
  urban_density_match: 0.9,
  modernization_level: 0.8,

  // Normative classification
  sentiment_in_city: "rude",
  prevalence: "common",
  respectability: "low",
  acceptability: "low",
  gender_specific: false,
  age_specific: false,

  // Context & importance
  relevance_for_travelers: "high",
  embarrassment_risk: "high",
  cultural_impact: "medium",

  context: {
    where: ["street_markets", "souvenir_shops", "malls"],
    when: ["anytime"],
    with_whom: "shopkeepers"
  },

  do_not: [
    "Expect prices to budge significantly",
    "Bargain with fixed-price retailers",
    "Insult quality of goods"
  ],
  tips: [
    "Bargaining is expected in street markets",
    "Start at 70% of asking price",
    "Be respectful and good-humored"
  ],

  embarrassment_level: 7,
  confidence_score: 0.92
})
```

#### Phrase Node
```cypher
CREATE (phrase:Phrase {
  id: "greeting_kannada_namaskara",
  english: "Hello/Greetings",
  language: "kannada",
  script: "Kannada",
  transliteration: "Namaskara",
  pronunciation: "/ˈnɑːmɑːskaːrɑː/",
  formality: "formal",
  context: "greeting",
  usage: {
    when: ["meeting_someone", "entering_shop", "formal_settings"],
    with_whom: ["elders", "strangers", "professionals"],
    cultural_note: "Shows respect when meeting Kannada speakers"
  },
  // Why this matters for Hindi speakers
  language_delta: {
    source_language: "Hindi",
    target_language: "Kannada",
    phonetic_similarity: 0.4,
    is_loanword_in_source: false,
    prerequisite_phrases: ["thank_you"],
    learning_priority: "critical"
  },
  audio_url: "https://audio.local-buddy.com/kannada_namaskara.mp3",
  video_url: "https://video.local-buddy.com/kannada_namaskara.mp4"
})
```

#### Restaurant Node
```cypher
CREATE (restaurant:Restaurant {
  id: "restaurant_xyz_mumbai",
  name: "Mahesh Lunch Home",
  city: "mumbai",
  area: "colaba",
  cuisine_types: ["seafood", "coastal_maharashtrian"],
  specialty_dishes: ["butter_garlic_crab", "tandoori_pomfret"],
  coordinates: {lat: 18.9235, lng: 72.8265},
  price_range: "expensive",
  average_cost_per_person: 1200,
  vegetarian_options: true,
  vegan_options: false,
  allergen_info: {nuts: true, dairy: true, shellfish: true},
  operating_hours: {open: "12:00", close: "23:30", break: null},
  ratings: {google: 4.5, zomato: 4.3, local_buddy: 4.6},
  ambiance: "casual_upscale",
  reservation_needed: true,
  seating_capacity: 150,
  contact: {phone: "+911234567890", website: "www.mahesh.com"},
  cultural_note: "Famous among locals and tourists for authentic coastal flavors"
})
```

#### Scheme Node (Government/Social Programs)
```cypher
CREATE (scheme:Scheme {
  id: "metro_pass_mumbai",
  name: "Mumbai Metro Smart Card",
  city: "mumbai",
  category: "public_transport",
  availability: "all_areas",
  eligibility: ["anyone"],
  benefits: [
    "Unlimited travel on metro",
    "Discounted fares",
    "24/7 access"
  ],
  cost: 100,
  documents_required: ["ID_proof"],
  how_to_apply: "Online at metro.local-buddy.com",
  processing_time_days: 1,
  duration_months: 12,
  relevance_for_travelers: "critical"
})
```

### 2. Edge Types & Relationships

```cypher
// Hierarchical Structure
City --HAS_AREA--> Area
Area --HAS_PLACE--> Place
Area --HAS_RESTAURANT--> Restaurant
Area --HAS_SCHEME_ACCESS--> Scheme

// Knowledge Dependencies
Phrase --PREREQUISITE--> Phrase
Norm --REQUIRES_CONTEXT--> Place
Norm --RELATED_TO--> Norm

// Cross-City Relationships (The Killer Feature)
(:Norm {title: "bargaining", city: "delhi"})
  --CONFLICTS_WITH-->
(:Norm {title: "bargaining", city: "bangalore"})
[confidence: 0.95, conflict_type: "taboo_vs_normal"]

(:Norm {title: "dressing", city: "gwalior"})
  --CONFLICTS_WITH-->
(:Norm {title: "dressing", city: "mumbai"})
[confidence: 0.88, conflict_type: "conservative_vs_liberal"]

// User Learning Path
Phrase --SIMILAR_TO--> Phrase [similarity: 0.85]
Norm --PREREQUISITE--> Norm [must_learn_first: true]
Place --REQUIRED_FOR_CONTEXT--> Norm

// Area Relationships
Area --SIMILAR_VIBE--> Area [similarity_score: 0.79]
Area --ADJACENT_TO--> Area
Area --GOOD_FOR--> Lifestyle [score: 0.9]

// Linguistic Relationships
Language --PHONEME_OVERLAP--> Language [shared_percent: 0.65]
Language --LOANWORD_FROM--> Language
Phrase --SAME_MEANING--> Phrase [confidence: 1.0]
```

---

## DATA LAYER ARCHITECTURE

### 1. Storage Strategy

```
┌────────────────────────────────────────────────┐
│          PERSISTENT DATA LAYER                 │
├────────────────────────────────────────────────┤
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ Neo4j (Knowledge Graph)                  │ │
│  │ ─────────────────────────────────────    │ │
│  │ • City structures & relationships         │ │
│  │ • Places, restaurants, areas              │ │
│  │ • Norms & cultural knowledge              │ │
│  │ • Cross-city conflict edges               │ │
│  │ • Language phrases & dependencies         │ │
│  │ • Schemes & opportunities                 │ │
│  │                                          │ │
│  │ Scale: ~5000-10000 nodes per city        │ │
│  │ Connections: ~50000-100000 edges per city│ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ PostgreSQL (User & Session Data)         │ │
│  │ ─────────────────────────────────────    │ │
│  │ • User profiles & preferences             │ │
│  │ • Learning state (retention scores)       │ │
│  │ • Chat history & sessions                 │ │
│  │ • User knowledge graph (what they know)   │ │
│  │ • Interaction logs for analytics          │ │
│  │                                          │ │
│  │ Schema: JSONB for flexible state         │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ MongoDB (Semi-Structured City Data)      │ │
│  │ ─────────────────────────────────────    │ │
│  │ • Raw scraped data before graph ingestion│ │
│  │ • Real-time data cache (weather, events) │ │
│  │ • Audit logs & data versioning           │ │
│  │                                          │ │
│  │ Collections:                             │ │
│  │ - attractions_raw                        │ │
│  │ - restaurants_raw                        │ │
│  │ - events_cache                           │ │
│  │ - safety_alerts                          │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ Elasticsearch (Search Index)             │ │
│  │ ─────────────────────────────────────    │ │
│  │ • Full-text search on all graph nodes    │ │
│  │ • Fuzzy matching for places/phrases      │ │
│  │ • User query indexing                    │ │
│  │                                          │ │
│  │ Documents indexed:                       │ │
│  │ - All places, phrases, norms per city    │ │
│  └──────────────────────────────────────────┘ │
│                                                │
└────────────────────────────────────────────────┘
        ↓ (sync every 6 hours)
┌────────────────────────────────────────────────┐
│        CACHING LAYER (Redis)                   │
├────────────────────────────────────────────────┤
│ • Hot graph nodes (popular places)   [30 min] │
│ • Real-time data (weather, traffic) [5-30 min]│
│ • User session state                [24 hours]│
│ • Query result cache                [15 min]  │
└────────────────────────────────────────────────┘
```

### 2. Graph Node Distribution Per City

#### Mumbai (Tier 1 - Largest)
```
Node Counts:
├─ City Core: 1 node
├─ Areas: 45-50 nodes (Bandra, Colaba, Andheri, etc.)
├─ Places: 150-200 nodes (attractions, landmarks)
├─ Restaurants: 200+ nodes
├─ Schemes: 25-30 nodes
├─ Norms/Cultural Info: 100-150 nodes
├─ Phrases: 150-200 nodes
└─ Total: ~700-750 nodes

Edge Counts:
├─ Hierarchical (city→area→place): ~300-400
├─ Cross-city conflicts: ~80-120
├─ Language prerequisites: ~150-200
├─ Similarity/relatedness: ~200-300
└─ Total: ~750-1000 edges
```

#### Ahmedabad (Tier 2)
```
Node Counts:
├─ City Core: 1 node
├─ Areas: 25-30 nodes
├─ Places: 80-100 nodes
├─ Restaurants: 100-120 nodes
├─ Schemes: 15-20 nodes
├─ Norms/Cultural Info: 60-80 nodes
├─ Phrases: 100-120 nodes
└─ Total: ~400-450 nodes

Edge Counts:
├─ Hierarchical: ~150-200
├─ Cross-city conflicts: ~40-60
├─ Language prerequisites: ~80-100
├─ Similarity/relatedness: ~100-150
└─ Total: ~400-500 edges
```

#### Gwalior (Tier 3)
```
Node Counts:
├─ City Core: 1 node
├─ Areas: 12-15 nodes
├─ Places: 40-50 nodes
├─ Restaurants: 50-60 nodes
├─ Schemes: 10-12 nodes
├─ Norms/Cultural Info: 30-40 nodes
├─ Phrases: 70-80 nodes
└─ Total: ~220-250 nodes

Edge Counts:
├─ Hierarchical: ~80-100
├─ Cross-city conflicts: ~20-30
├─ Language prerequisites: ~40-50
├─ Similarity/relatedness: ~50-70
└─ Total: ~200-250 edges
```

---

## DATA FLOW & PROCESSING

### 1. Initial Data Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              DATA COLLECTION PHASE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  SOURCES:                                                   │
│  ├─ Google Maps API (attractions, ratings, hours)          │
│  ├─ Zomato API (restaurants)                               │
│  ├─ Web scraping (reviews, local blogs)                    │
│  ├─ Government APIs (schemes, public transport)            │
│  └─ Manual curation (norms, cultural info)                 │
│                                                             │
│                    ↓                                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Raw Data Storage (MongoDB)                         │   │
│  │ • attractions_raw                                  │   │
│  │ • restaurants_raw                                  │   │
│  │ • cultural_data_raw                                │   │
│  │ • schemes_raw                                      │   │
│  └────────────────────────────────────────────────────┘   │
│                    ↓                                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Schema Validation & Cleaning                       │   │
│  │ • Validate against data models                     │   │
│  │ • Remove duplicates                                │   │
│  │ • Fix missing data with LLM                        │   │
│  │ • Normalize phone numbers, URLs, etc.              │   │
│  └────────────────────────────────────────────────────┘   │
│                    ↓                                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Feature Vector Generation (LLM)                    │   │
│  │ • Formality level [0-1]                            │   │
│  │ • Collectivist score [0-1]                         │   │
│  │ • Urban density match [0-1]                        │   │
│  │ • Culture vibe classification                      │   │
│  └────────────────────────────────────────────────────┘   │
│                    ↓                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Conflict Detection (Automated Cypher Queries)      │   │
│  │ • Find same-domain norms with opposite sentiment   │   │
│  │ • Score confidence of conflicts                    │   │
│  │ • Flag for human review if < 0.85 confidence      │   │
│  └────────────────────────────────────────────────────┘   │
│                    ↓                                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Neo4j Graph Ingestion                              │   │
│  │ • Create nodes from validated data                 │   │
│  │ • Create hierarchical edges                        │   │
│  │ • Create conflict edges                            │   │
│  │ • Create similarity edges                          │   │
│  └────────────────────────────────────────────────────┘   │
│                    ↓                                        │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Elasticsearch Index Creation                       │   │
│  │ • Index all nodes for full-text search             │   │
│  │ • Set up fuzzy matching                            │   │
│  └────────────────────────────────────────────────────┘   │
│                    ↓                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ READY FOR PERSONALIZATION ENGINE                   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. User Request Flow with Knowledge Graph

```
USER REQUEST: "I'm moving to Bangalore from Delhi. Help me prepare."
         │
         ▼
┌─────────────────────────────────────┐
│ 1. INTENT CLASSIFICATION            │
│ ├─ Extract origin: Delhi            │
│ ├─ Extract destination: Bangalore   │
│ ├─ Extract purpose: relocation      │
│ └─ Extract interests: culture, norms│
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 2. USER CONTEXT FETCH (PostgreSQL)  │
│ ├─ Load user profile                │
│ ├─ Load knowledge state              │
│ └─ Load learning history             │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. GAP ANALYSIS (Graph Query)                              │
│                                                             │
│ Query: MATCH (n:Norm)-[:NORMAL_IN]->(origin:City)         │
│        WHERE origin.name = "Delhi"                         │
│        RETURN DISTINCT n                                   │
│                                                             │
│ Result: 120 norms user likely knows                        │
│                                                             │
│ Query: MATCH (m:Norm)-[:NORMAL_IN]->(dest:City)           │
│        WHERE dest.name = "Bangalore"                       │
│        RETURN DISTINCT m, m.importance                     │
│                                                             │
│ Result: 140 norms user needs to learn                      │
│                                                             │
│ Delta = 140 - (overlap with Delhi) = ~90 new norms        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CONFLICT PRIORITIZATION (Cross-City Graph Query)        │
│                                                             │
│ Query: MATCH (delhi_norm:Norm)-[:NORMAL_IN]->(delhi:City) │
│        WHERE delhi.name = "Delhi"                          │
│        MATCH (bangalore_norm:Norm)-[:CONFLICTS_WITH]->     │
│           (delhi_norm)                                      │
│        WHERE (bangalore_norm)-[:NORMAL_IN]->(bangalore_cty)│
│        AND bangalore_cty.name = "Bangalore"                │
│        RETURN delhi_norm, bangalore_norm,                  │
│               bangalore_norm.embarrassment_level           │
│        ORDER BY embarrassment_level DESC                   │
│                                                             │
│ Result: Top 15 HIGH-CONFLICT norms                         │
│ Examples:                                                   │
│ • "Bargaining in markets" (normal Delhi, rude Bangalore)   │
│ • "Spitting in public" (ignored Delhi, taboo Bangalore)    │
│ • "Loud speaking" (normal Delhi, annoys Bangalore)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. PERSONALIZED LEARNING PATH (Path Planning)              │
│                                                             │
│ Strategy:                                                   │
│ 1. Sort by conflict embarrassment score (DESC)             │
│ 2. Add prerequisites (language → phrases → culture)        │
│ 3. Group by area (areas with most conflicts first)         │
│ 4. Consider user time availability (hours/weeks)           │
│                                                             │
│ Weighted Ranking Formula:                                   │
│ P(norm) = (0.4 * conflict_score)                           │
│         + (0.3 * cultural_importance)                      │
│         + (0.2 * prerequisite_satisfied)                   │
│         + (0.1 * user_interest_match)                      │
│                                                             │
│ Output: Prioritized list of 20-30 "must learn" nodes      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. CONTEXT ENRICHMENT (Multi-Source Data)                  │
│                                                             │
│ For top 20 prioritized norms, fetch:                       │
│                                                             │
│ • Related Places (Graph):                                   │
│   WHERE (norm)-[:REQUIRED_FOR_CONTEXT]->(place)            │
│   → Show "Bargaining happens at Crawford Market"           │
│                                                             │
│ • Related Areas (Graph):                                    │
│   WHERE (norm)-[:PREVALENT_IN]->(area)                     │
│   → Show "Predominant in business districts"               │
│                                                             │
│ • Real-Time Data (Redis/Events):                           │
│   → "Crawford Market is closed Sundays"                    │
│   → "Festivals this month: X, Y, Z"                        │
│                                                             │
│ • Language Support (Graph):                                │
│   WHERE (phrase)-[:USEFUL_FOR]->(norm)                     │
│   → Show relevant Kannada phrases to know                  │
│                                                             │
│ • Related Norms (Similarity Edges):                         │
│   WHERE (norm)-[:SIMILAR_TO]->(other_norm)                │
│   → Show "Similar to haggling in morning markets"         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. AGENT SYNTHESIS & RESPONSE GENERATION                   │
│                                                             │
│ Claude API receives:                                        │
│ - User request context                                      │
│ - Prioritized norm list                                     │
│ - Related places & areas                                    │
│ - Real-time events & safety data                            │
│ - User learning history                                     │
│                                                             │
│ Claude generates natural language response:                 │
│ "Based on your move from Delhi to Bangalore,              │
│  here are the top 5 cultural clashes you should know...   │
│  [customized based on graph data]"                         │
│                                                             │
│ Response includes:                                          │
│ ✓ Top conflicts with explanations                          │
│ ✓ Places to practice learning                              │
│ ✓ Kannada phrases to know                                  │
│ ✓ Safety guidance by area                                  │
│ ✓ Real-time events relevant to learning                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. TRACK & UPDATE USER STATE (PostgreSQL)                 │
│                                                             │
│ Save to user.knowledge_state:                              │
│ {                                                           │
│   "norm_bargaining_markets": {                             │
│     "seen": true,                                          │
│     "timestamp": "2026-06-06T10:30:00Z",                  │
│     "retention_score": null,  // pending user interaction  │
│     "priority": 1,                                         │
│     "module_completed": false                              │
│   },                                                        │
│   "norm_loud_speaking": {                                  │
│     "seen": true,                                          │
│     "retention_score": null,                               │
│     "priority": 2                                          │
│   },                                                        │
│   ...                                                       │
│ }                                                           │
│                                                             │
│ Enable spaced repetition for low-retention items          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
USER RECEIVES PERSONALIZED, CONFLICT-PRIORITIZED RESPONSE
```

### 3. Real-Time Data Integration Flow

```
EXTERNAL SERVICES (Updated on Schedule)
┌──────────────┬──────────────┬────────────┬────────────┐
│ Weather API  │ Traffic API  │ Events API │ Safety News│
│ (30 min)     │ (5 min)      │ (24 hr)    │ (24 hr)    │
└──────────────┴──────────────┴────────────┴────────────┘
         │             │             │             │
         └─────────────┴─────────────┴─────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │ MongoDB Real-Time Cache │
         ├─────────────────────────┤
         │ • events_cache          │
         │ • weather_snapshot      │
         │ • traffic_conditions    │
         │ • safety_alerts         │
         └─────────────────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │ Redis Hot Cache         │
         ├─────────────────────────┤
         │ TTL: 5-30 min           │
         │ Quick access for agents │
         └─────────────────────────┘
                      │
                      ▼
         (Agent queries during request processing)

         Query: "What events are happening in Bangalore
                 near attractions I'm planning to visit?"

         ├─ Check Redis (instant if fresh)
         ├─ If stale, fetch from MongoDB
         ├─ Merge with graph place data
         └─ Return enriched context
```

---

## MULTI-CITY SCALING STRATEGY

### The Problem: Adding a New City Without O(n²) Manual Work

When adding a 4th, 5th, 10th city, you need to:
1. Add the city's own knowledge (intra-city structure)
2. Connect it to all existing cities (inter-city conflicts & similarities)

**Manual approach** = 45 city-pairs for 10 cities = massive curation burden

**Smart approach** = Use feature vectors to compute relationships automatically

### Solution: Automated Conflict Detection Pipeline

```
NEW CITY ADDED: "Pune"
         │
         ▼
┌──────────────────────────────────┐
│ 1. INTRA-CITY DATA COLLECTION    │
│                                  │
│ Sources:                         │
│ ├─ Google Maps (attractions)    │
│ ├─ Zomato (restaurants)         │
│ ├─ Local experts (cultural data)│
│ └─ Manual curation (norms)      │
│                                  │
│ Result: ~400-500 new nodes       │
│ Status: ISOLATED GRAPH           │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 2. FEATURE VECTOR GENERATION     │
│    (LLM-Powered)                 │
│                                  │
│ For each Norm, compute:          │
│ • formality_level ∈ [0,1]        │
│ • collectivist_score ∈ [0,1]     │
│ • urban_density_match ∈ [0,1]    │
│ • modernization_level ∈ [0,1]    │
│ • temperature (weather match)    │
│ • cultural_emphasis_idx          │
│                                  │
│ Confidence: Use LLM annotation   │
│ + human spot-check on 10% sample│
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 3. AUTOMATED CONFLICT DETECTION  │
│                                  │
│ Cypher Query:                    │
│ MATCH (pune_norm:Norm)           │
│       {city: "Pune"}             │
│       (existing_norm:Norm)       │
│       {city: IN ["Delhi",        │
│              "Mumbai",           │
│              "Bangalore"]}       │
│ WHERE pune_norm.tags ∩           │
│       existing_norm.tags != ∅    │
│   AND cosine_similarity(         │
│         pune_norm.features,      │
│         existing_norm.features)  │
│       > 0.6 // Same domain       │
│   AND pune_norm.sentiment !=     │
│       existing_norm.sentiment    │
│ RETURN pune_norm, existing_norm, │
│   similarity_score,              │
│   confidence_score               │
│ ORDER BY confidence_score DESC   │
│                                  │
│ Result: ~120-150 potential       │
│ conflicts detected               │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 4. SIMILARITY DETECTION          │
│                                  │
│ Cypher Query:                    │
│ MATCH (pune_area:Area)           │
│       {city: "Pune"}             │
│       (existing_area:Area)       │
│       {city: IN ["Bangalore"...]}│
│ WHERE cosine_similarity(         │
│         pune_area.features,      │
│         existing_area.features)  │
│       > 0.75 // Very similar     │
│ RETURN pune_area, existing_area, │
│   similarity_score               │
│                                  │
│ Creates edges like:              │
│ Koregaon_Park --SIMILAR_TO-->    │
│   Whitefield (similarity: 0.82)  │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 5. LOW-CONFIDENCE FLAGGING       │
│                                  │
│ Confidence < 0.80?               │
│ → Flag for human review          │
│ → Display to local Pune experts  │
│ → Upvote/downvote automatically  │
│   computes consensus              │
│                                  │
│ High confidence (>0.90)?         │
│ → Auto-accepted to graph         │
└──────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ 6. GRAPH UPDATE                  │
│                                  │
│ CREATE (pune_norm)-              │
│   [:CONFLICTS_WITH]->            │
│   (mumbai_norm)                  │
│ SET conflict.confidence = 0.92   │
│     conflict.human_verified = ?  │
│     conflict.source = "auto"     │
│                                  │
│ Result: Pune integrated into     │
│ full graph in 2-3 days, not weeks│
└──────────────────────────────────┘
```

### Cost Analysis: Manual vs. Automated Approach

```
Adding City #4 (Pune):

MANUAL APPROACH:
├─ Collect data: 5 days
├─ Hand-curate norms: 3 days
├─ Manually create conflict edges: 8 days
│  (3 x 45 pairs = 135 individual edge creations)
├─ Manual verification: 3 days
└─ Total: ~19 days (3 person-weeks)

FEATURE VECTOR + AUTO-DETECTION APPROACH:
├─ Collect data: 5 days
├─ LLM tag features: 0.5 days (automated)
├─ Run conflict detection: 0.5 days (automated)
├─ Human QA (only flagged items): 1 day
│  (~20% of edges need review, not 100%)
├─ Consensus voting: 1 day (crowd)
└─ Total: ~8 days (1 person-week + crowd)

Savings: 60% faster, 75% less labor
```

---

## USER MODEL & PERSONALIZATION

### 1. User Model Schema (PostgreSQL)

```sql
CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  origin_city VARCHAR(100) NOT NULL,
  destination_city VARCHAR(100) NOT NULL,
  purpose ENUM('job', 'study', 'relocation', 'travel', 'business'),
  created_at TIMESTAMP DEFAULT NOW(),

  // Learner profile
  learning_goal VARCHAR(255),
  time_available_hours INT,  // hours per week
  preferences JSONB,  // {interests: [...], accessibility: {...}}

  // Knowledge tracking
  knowledge_state JSONB,  // {node_id: {seen, retention, priority}, ...}

  // Analytics
  total_learning_time_hours INT DEFAULT 0,
  total_nodes_seen INT DEFAULT 0,
  average_retention_score FLOAT DEFAULT 0.0,
  last_active_at TIMESTAMP,

  // Settings
  notification_preferences JSONB,
  privacy_settings JSONB
);

CREATE TABLE user_interactions (
  interaction_id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(user_id),
  node_id VARCHAR(255) NOT NULL,  // references graph node
  interaction_type ENUM('viewed', 'bookmarked', 'completed', 'struggled'),
  timestamp TIMESTAMP DEFAULT NOW(),
  time_spent_seconds INT,
  retention_score FLOAT,  // 0-1, post-quiz

  INDEX(user_id, timestamp)
);

CREATE TABLE user_learning_state (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(user_id),
  node_id VARCHAR(255) NOT NULL,

  // Spaced Repetition (SM-2 Algorithm)
  easiness_factor FLOAT DEFAULT 2.5,
  interval_days INT DEFAULT 1,
  repetitions INT DEFAULT 0,
  next_review_date DATE,

  // Learning Progress
  mastery_level ENUM('new', 'seen', 'learning', 'practicing', 'mastered'),
  last_reviewed_at TIMESTAMP,
  review_count INT DEFAULT 0,

  UNIQUE(user_id, node_id)
);
```

### 2. Personalization Algorithm

```python
def generate_personalized_learning_path(user_id: str) -> List[str]:
    """
    Generate ordered list of graph nodes for user to learn

    Returns: [node_id_1, node_id_2, ..., node_id_20]
    ordered by personalized importance score
    """

    # 1. Get user context
    user = fetch_from_postgres(user_id)
    knowledge_state = user.knowledge_state

    # 2. Query graph for delta (what they don't know)
    city_graph = fetch_city_subgraph(user.destination_city)
    all_nodes = city_graph.nodes()
    seen_nodes = set(knowledge_state.keys())
    delta_nodes = all_nodes - seen_nodes

    # 3. Score each node
    node_scores = {}
    for node_id in delta_nodes:
        node = get_graph_node(node_id)

        # Component 1: Conflict importance
        conflict_score = calculate_conflict_importance(
            node,
            user.origin_city,
            user.destination_city
        )  # [0, 1]

        # Component 2: Prerequisites satisfied
        prerequisite_score = calculate_prerequisite_satisfaction(
            node, knowledge_state
        )  # [0, 1]

        # Component 3: User interest match
        interest_score = calculate_interest_match(
            node, user.preferences
        )  # [0, 1]

        # Component 4: Time allocation
        time_score = estimate_learning_time(node, user.time_available_hours)

        # Weighted combination
        node_scores[node_id] = (
            0.40 * conflict_score +
            0.30 * prerequisite_score +
            0.20 * interest_score +
            0.10 * time_score
        )

    # 4. Sort by score
    ranked_nodes = sorted(
        node_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]  # Top 20

    return [node_id for node_id, _ in ranked_nodes]


def calculate_conflict_importance(node, origin, destination):
    """
    Check if this norm has conflicts between origin & destination

    Returns high score if:
    - Norm exists in origin & destination with opposite sentiment
    - High embarrassment risk if violated
    """

    # Cypher query
    query = """
    MATCH (origin_norm:Norm)-[:NORMAL_IN]->(origin:City)
    WHERE origin.name = $origin_city
    MATCH (dest_norm:Norm)-[:CONFLICTS_WITH]->(origin_norm)
    WHERE (dest_norm)-[:NORMAL_IN]->(dest:City)
    AND dest.name = $destination_city
    AND dest_norm.id = $node_id
    RETURN dest_norm.embarrassment_level,
           dest_norm.confidence_score
    """

    result = neo4j_query(query, {
        'origin_city': origin,
        'destination_city': destination,
        'node_id': node.id
    })

    if result:
        embarrassment = result[0]['embarrassment_level']
        confidence = result[0]['confidence_score']
        return (embarrassment / 10) * confidence  # Normalize & weight by confidence
    else:
        return 0.0  # No direct conflict found


def calculate_prerequisite_satisfaction(node, knowledge_state):
    """
    Check if user has learned prerequisites for this node

    Returns 1.0 if all prerequisites seen
    Returns 0.0 if critical prerequisites missing
    """

    # Get prerequisites from graph
    prerequisites = get_node_prerequisites(node.id)

    satisfied = sum(1 for prereq in prerequisites
                    if prereq in knowledge_state)

    if len(prerequisites) == 0:
        return 1.0  # No prerequisites

    satisfaction = satisfied / len(prerequisites)

    # Penalty: Don't push if critical prereq missing
    if satisfaction < 0.5 and has_critical_prerequisite(prerequisites):
        return 0.2  # De-prioritize

    return satisfaction


def calculate_interest_match(node, user_preferences):
    """
    Does this node match user's stated interests?

    Returns 1.0 if strong match
    Returns 0.0 if irrelevant to interests
    """

    node_tags = set(node.tags)
    user_interests = set(user_preferences['interests'])

    if not user_interests:
        return 0.5  # Neutral if no preferences stated

    intersection = node_tags & user_interests
    return len(intersection) / max(len(user_interests), 1)
```

### 3. Spaced Repetition Integration

```
FLOW: User completes a module
         │
         ▼
POST-MODULE QUIZ (Retention Score 0-1)
         │
         ├─ Score > 0.8? (Mastered)
         │  └─ interval = 21 days (long gap)
         │
         ├─ Score 0.5-0.8? (Learning)
         │  └─ interval = 3 days (practice more)
         │
         └─ Score < 0.5? (Struggling)
            └─ interval = 1 day (daily review)
                         │
                         ▼
         UPDATE user_learning_state:
         ├─ next_review_date = today + interval
         ├─ repetitions += 1
         ├─ mastery_level = "practicing"
         └─ last_reviewed_at = now
                         │
                         ▼
         BACKGROUND JOB (Daily):
         ├─ Find due items (next_review_date <= today)
         ├─ Re-queue for user's tomorrow
         └─ Surface to user at right moment
```

---

## REAL-TIME INTEGRATION

### 1. Real-Time Data Sync Architecture

```
EXTERNAL SERVICES
├─ OpenWeatherMap (weather)
├─ Google Maps (traffic)
├─ Zomato (restaurant hours)
├─ Event APIs (festivals)
└─ Local news RSS (safety)
        │
        ▼
CELERY TASK SCHEDULER
├─ weather_refresh_task (every 30 min)
├─ traffic_refresh_task (every 5 min)
├─ events_refresh_task (every 24 hr)
├─ restaurant_refresh_task (every 2 hr)
└─ safety_alerts_task (every 6 hr)
        │
        ▼
MONGODB CACHE (Real-time collections)
- events_bangalore_2026_06
- weather_snapshot_bangalore
- traffic_conditions_bangalore
- safety_alerts_bangalore
        │
        ▼
REDIS HOT CACHE (5-30 min TTL)
- rtd:weather:bangalore
- rtd:events:bangalore
- rtd:traffic:bangalore
        │
        ▼
AGENT QUERIES
"What can I do in Bangalore this weekend?"
├─ Check Redis (events + weather)
├─ Cross-reference graph (places open)
└─ Return integrated response
```

### 2. How Real-Time Data Enhances Graph Queries

```
EXAMPLE SCENARIO:
User asks: "Should I visit Gateway of India today?"

AGENT EXECUTION:

Step 1: Query Graph
MATCH (place:Place {name: "Gateway of India"})
RETURN place.hours, place.duration, place.best_time

Result: Opening hours, usual crowd levels

Step 2: Fetch Real-Time Data
├─ Weather Redis key: rtd:weather:mumbai
│  └─ {temp: 35°C, humidity: 88%, rain: 0%}
│
├─ Traffic Redis key: rtd:traffic:colaba
│  └─ Current commute from user location: 20 min
│
└─ Events/Safety: MongoDB
   └─ No alerts or closures today

Step 3: Synthesize Response
"Yes, good day to visit!
 • Weather: Hot & humid, bring water
 • Travel time: 20 min by taxi
 • Crowd level: High (afternoon), medium (early morning)
 • Recommendation: Go early morning (7-9 AM)"
```

---

## TECHNICAL IMPLEMENTATION

### 1. Tech Stack Integration Map

```
┌─────────────────────────────────────────────────┐
│              FRONTEND LAYER                     │
│  (React Native / Next.js)                       │
│  ├─ Chat interface                              │
│  ├─ Learning modules                            │
│  └─ Progress dashboard                          │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│           API GATEWAY (FastAPI)                 │
│  ├─ /chat/message POST                          │
│  ├─ /learning/path GET                          │
│  ├─ /graph/search POST                          │
│  └─ /realtime/{type}/{city} GET                 │
└────┬───────┬────────┬────────────┬──────────────┘
     │       │        │            │
┌────▼─┐ ┌───▼──┐ ┌──▼──┐ ┌──────▼─────┐
│ Core │ │Data  │ │Real- │ │ External   │
│Agent │ │Repo  │ │Time  │ │ Services   │
│      │ │      │ │Svc   │ │            │
│Claude│ │  ↓   │ │  ↓   │ │ Weather API│
│API   │ │  ↓   │ │  ↓   │ │ Maps API   │
└──────┘ │  ↓   │ │  ↓   │ │ Zomato API │
         │  ↓   │ │ Redis│ │ Events API │
         └──┬───┘ │Cache │ │ + RSS      │
            │     │      │ │            │
            │     └──┬───┘ └────────────┘
            │        │
    ┌───────┴────────┴────────────┐
    │   PERSISTENCE LAYER        │
    ├───────────────────────────┐ │
    │ Neo4j (Knowledge Graph)   │ │
    │ • City structures         │ │
    │ • Cross-city conflicts    │ │
    │ • Learning dependencies   │ │
    └───────────────────────────┘ │
    ├───────────────────────────┐ │
    │ PostgreSQL (User Data)    │ │
    │ • User profiles           │ │
    │ • Learning state          │ │
    │ • Session data            │ │
    └───────────────────────────┘ │
    ├───────────────────────────┐ │
    │ MongoDB (Raw/Cache Data)  │ │
    │ • Scraped data            │ │
    │ • Real-time snapshots     │ │
    │ • Audit logs              │ │
    └───────────────────────────┘ │
    ├───────────────────────────┐ │
    │ Elasticsearch (Search)    │ │
    │ • Full-text place search  │ │
    │ • Fuzzy phrase matching   │ │
    └───────────────────────────┘ │
    └───────────────────────────┘
```

### 2. Core Neo4j Queries Reference

```cypher
# Query 1: Find norms user doesn't know but destination city has
MATCH (user_origin:City {name: $origin_city}),
      (user_dest:City {name: $destination_city})
MATCH (dest_norm:Norm)-[:NORMAL_IN]->(user_dest)
WHERE NOT EXISTS(
  (origin_norm:Norm)-[:NORMAL_IN]->(user_origin)
  AND (dest_norm)-[:IDENTICAL_TO]->(origin_norm)
)
RETURN dest_norm
ORDER BY dest_norm.importance_level DESC
LIMIT 20;

# Query 2: Find high-conflict norms (taboo in dest, normal in origin)
MATCH (origin_norm:Norm)-[:NORMAL_IN]->(origin:City)
WHERE origin.name = $origin_city
MATCH (origin_norm)-[:CONFLICTS_WITH]->(dest_norm:Norm)
WHERE (dest_norm)-[:NORMAL_IN]->(dest:City)
AND dest.name = $destination_city
AND dest_norm.taboo = true
RETURN origin_norm, dest_norm,
       dest_norm.embarrassment_level,
       dest_norm.conflict_type
ORDER BY dest_norm.embarrassment_level DESC;

# Query 3: Find prerequisites before learning a norm
MATCH (norm:Norm {id: $norm_id})
MATCH (prerequisite)-[:PREREQUISITE_FOR]->(norm)
RETURN prerequisite
ORDER BY prerequisite.importance DESC;

# Query 4: Find similar areas based on feature vectors
WITH $area_features AS query_features
MATCH (area:Area {city: $city})
WHERE vector_similarity(area.feature_vector, query_features) > $threshold
RETURN area, vector_similarity(area.feature_vector, query_features) AS similarity
ORDER BY similarity DESC
LIMIT 5;

# Query 5: Build complete context for a place
MATCH (place:Place {id: $place_id})
OPTIONAL MATCH (place)-[:IN_AREA]->(area:Area)
OPTIONAL MATCH (place)-[:REQUIRES_UNDERSTANDING]->(norm:Norm)
OPTIONAL MATCH (norm)-[:CONFLICTS_WITH]->(conflict_norm:Norm)
RETURNING {
  place: place,
  area: area,
  norms_to_know: COLLECT(norm),
  potential_conflicts: COLLECT(conflict_norm)
};
```

### 3. Data Flow Implementation Classes

```python
# core/graph_engine.py
from neo4j import GraphDatabase

class GraphEngine:
    """Interface to Neo4j knowledge graph"""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def get_learning_priority(self, user_id: str,
                             destination_city: str) -> List[str]:
        """
        Get prioritized list of nodes for user to learn

        Algorithm:
        1. Get user's known nodes (from PostgreSQL)
        2. Query graph for destination city nodes
        3. Calculate conflict scores
        4. Rank by importance
        5. Return top 20
        """
        with self.driver.session() as session:
            # Implementation here
            pass

    def detect_conflicts(self, origin_city: str,
                        dest_city: str) -> List[Tuple]:
        """Auto-detect conflicting norms between cities"""
        query = """
        MATCH (origin_norm:Norm)-[:NORMAL_IN]->(origin:City)
        WHERE origin.name = $origin
        MATCH (origin_norm)-[:CONFLICTS_WITH]->(dest_norm:Norm)
        WHERE (dest_norm)-[:NORMAL_IN]->(dest:City)
        AND dest.name = $destination
        RETURN origin_norm, dest_norm,
               dest_norm.confidence_score
        ORDER BY dest_norm.embarrassment_level DESC
        """
        result = session.run(query, {
            'origin': origin_city,
            'destination': dest_city
        })
        return result.data()


# data/user_model.py
from sqlalchemy import create_engine, Column, String, JSONB
from sqlalchemy.orm import Session

class UserModel:
    """Interface to PostgreSQL user data"""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def track_interaction(self, user_id: str, node_id: str,
                         interaction_type: str,
                         retention_score: float):
        """Record user learning interaction for spaced repetition"""
        # Implementation
        pass

    def get_learning_state(self, user_id: str) -> Dict:
        """Fetch user's knowledge state from PostgreSQL"""
        # Implementation
        pass


# realtime/data_sync.py
from celery import Celery

app = Celery('local_buddy', broker='redis://localhost:6379')

@app.task(bind=True)
def sync_weather_data(self):
    """Background job: refresh weather data every 30 min"""
    for city in ['mumbai', 'ahmedabad', 'gwalior']:
        weather = OpenWeatherMapAPI.get_weather(city)
        MongoDBCache.update('weather_snapshot_{}'.format(city), weather)
        RedisCache.set('rtd:weather:{}'.format(city), weather, ttl=1800)

@app.task(bind=True)
def detect_and_add_page_conflicts(self):
    """Background job: detect conflicts when new city added"""
    new_cities = get_newly_added_cities()
    for city in new_cities:
        conflicts = auto_detect_conflicts(city)
        flag_low_confidence_for_review(conflicts)
        create_high_confidence_edges(conflicts)
```

---

## DATA QUALITY & EVOLUTION

### 1. Quality Assurance Pipeline

```
NEW DATA ENTRY
         │
         ▼
┌─────────────────────────────────────┐
│ Schema Validation                   │
│ • Check required fields             │
│ • Validate data types               │
│ • Phone number formatting           │
│ • Coordinate bounds checking        │
└─────────────────────────────────────┘
         │
         ├─ FAIL → Return errors to data collector
         │
         ▼
┌─────────────────────────────────────┐
│ Duplicate Detection                 │
│ • Fuzzy match on names              │
│ • Coordinate proximity check        │
│ • Phone number comparison           │
└─────────────────────────────────────┘
         │
         ├─ FOUND DUPLICATE → Merge & flag
         │
         ▼
┌─────────────────────────────────────┐
│ LLM Feature Tagging                 │
│ • Generate feature vectors          │
│ • Set conflict scores               │
│ • Classify cultural importance      │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Confidence Assessment               │
│ • Feature confidence > 0.90?        │
│ • Conflict confidence > 0.85?       │
└─────────────────────────────────────┘
         │
         ├─ LOW confidence → Flag for human QA
         │
         ▼
┌─────────────────────────────────────┐
│ Ready for Graph Entry               │
└─────────────────────────────────────┘
```

### 2. Feedback Loop: Learning from User Interactions

```
USER INTERACTION
├─ User sees norm: "Bargaining in markets taboo"
├─ User's feedback: "Actually it's accepted here!"
└─ Confidence score updated based on votes
         │
         ▼
AGGREGATE FEEDBACK
├─ Track conflict edges that users often disagree with
├─ Identify outdated information
└─ Flag for expert review
         │
         ▼
EXPERT REVIEW
├─ Local experts verify disagreements
├─ Update confidence scores
└─ Re-train LLM feature detector
         │
         ▼
CONTINUOUS IMPROVEMENT
          Graph edges improve accuracy over time
```

### 3. Data Versioning & Rollback

```
Every graph modification creates an audit record:

{
  timestamp: "2026-06-06T10:30:00Z",
  edge_modified: "bargaining_Market_Delhi → Bangalore",
  old_confidence: 0.92,
  new_confidence: 0.88,
  reason: "User feedback corrected",
  source: "crowd_vote",
  total_votes: 15,
  consensus: 0.87,
  human_verified: false,
  can_rollback_to: "2026-06-05T00:00:00Z"
}
```

---

## IMPLEMENTATION PHASES

### Phase 1: Foundation (Weeks 1-4)
```
✓ Set up Neo4j instance
✓ Define complete graph schema
✓ PostgreSQL user model
✓ FastAPI API skeleton
✓ Initial 1 city (Mumbai) data load
```

### Phase 2: Core System (Weeks 5-8)
```
✓ Orchestrator agent implementation
✓ Gap analysis + conflict detection
✓ User personalization engine
✓ Spaced repetition integration
✓ Add 2nd city (Ahmedabad)
```

### Phase 3: Real-Time & Scale (Weeks 9-12)
```
✓ Real-time data integration
✓ Auto-conflict detection for new cities
✓ Add 3rd city (Gwalior)
✓ Scale testing
```

### Phase 4: Polish & Launch (Weeks 13-14)
```
✓ QA & bug fixes
✓ Performance optimization
✓ User feedback integration
✓ Launch MVP
```

---

## KEY SUCCESS METRICS

### Graph Quality
- Edge confidence scores (target: 0.85+)
- Conflict detection accuracy (target: 92%+)
- User disagreement rate (target: <5%)

### Personalization Effectiveness
- Retention score improvement (target: 20% week-over-week)
- Completion rate of suggested modules (target: 60%+)
- Time-to-value (target: <7 days)

### System Performance
- Graph query latency (target: <200ms)
- API response time (target: <2s)
- Cache hit rate (target: >80%)

### User Engagement
- Daily active users (target: 10%+)
- Module completion rate (target: 40%+)
- Review cycle participation (target: 30%+)

---

## MVP SCOPE & BUILD PLAN

### MVP Definition: "Bangalore → Ahmedabad Relocation Assistant"

**Scope:**
- 1 route: Bangalore → Ahmedabad only
- 2 user personas: Relocating professional + Traveler
- Core features: Conflict detection + Area recommendations + Quick setup
- No real-time data (MVP v1)
- No mobile app (web only, MVP v1)

**Realistic Timeline:** 8 weeks (not 14)

---

### WEEK 1: Core Infrastructure Setup

#### Goal: Get databases running + basic API working

```
DELIVERABLES:
✓ Neo4j instance (local Docker)
✓ PostgreSQL database (local)
✓ FastAPI skeleton with /health endpoint
✓ Graph schema defined in Cypher
✓ First city (Ahmedabad) structure created

TIME: 3 days (if you know Docker)

TASKS:

1. Docker Setup (Day 1 - 3 hours)
   └─ docker-compose.yml for Neo4j + PostgreSQL
   └─ Get both running locally

2. Graph Schema Creation (Day 1-2 - 8 hours)
   └─ Create Cypher schema file: schema.cypher
   └─ Define node types:
      ├─ City
      ├─ Area
      ├─ Place
      ├─ Norm
      ├─ Restaurant
      ├─ CostOfLiving (NEW!)
      ├─ School (NEW!)
      └─ QuickSetup (NEW!)

   └─ Define edge types:
      ├─ HAS_AREA
      ├─ HAS_PLACE
      ├─ CONFLICTS_WITH
      ├─ SIMILAR_VIBE_TO (NEW!)
      ├─ SAFE_FOR_GENDER (NEW!)
      └─ REQUIRES_CONTEXT

3. Python Project Structure (Day 2-3 - 5 hours)
   └─ Create project skeleton:
      ├─ FastAPI app (main.py)
      ├─ Neo4j driver setup (graph_engine.py)
      ├─ PostgreSQL models (user_model.py)
      ├─ Config files
      └─ Basic requirements.txt

4. First Test (Day 3 - 1 hour)
   └─ Create city "Ahmedabad" node in Neo4j
   └─ Test connection from Python
   └─ Verify /health endpoint works

COMMANDS TO RUN:
```bash
# 1. Create docker-compose.yml (see template below)
# 2. Start services
docker-compose up -d

# 3. Initialize Python env
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn neo4j psycopg2-binary python-dotenv

# 4. Run basic API
uvicorn main:app --reload

# 5. Visit http://localhost:8000/health
```

#### docker-compose.yml Template:
```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.10
    environment:
      NEO4J_AUTH: neo4j/password123
    ports:
      - "7687:7687"
      - "7474:7474"
    volumes:
      - neo4j_data:/data

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: localbuddy
      POSTGRES_PASSWORD: secure123
      POSTGRES_DB: localbuddy_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  neo4j_data:
  postgres_data:
```

---

### WEEK 2: Data Loading - Ahmedabad

#### Goal: Get ~500 nodes into Neo4j for Ahmedabad

```
DELIVERABLES:
✓ 50-60 Ahmedabad attractions loaded
✓ 60+ restaurants loaded
✓ 30-40 hotels loaded
✓ 10-12 cultural norms (Ahmedabad-specific)
✓ 5-6 cost of living data points
✓ 3-4 schools
✓ Cross-conflict edges with Bangalore (manually created)

TIME: 4 days

TASKS:

1. Data Collection (Day 1-2 - 8 hours)
   └─ Use Google Maps API to fetch:
      ├─ Attractions (search "tourist_attraction" in Ahmedabad)
      ├─ Restaurants (search "restaurant")
      └─ Hotels (search "hotel")

   └─ Manual creation (Google Sheets → JSON):
      ├─ Cultural norms (10 critical ones)
      ├─ Cost of living data
      └─ Schools

   └─ Create JSON files:
      ├─ ahmedabad/attractions.json
      ├─ ahmedabad/restaurants.json
      ├─ ahmedabad/hotels.json
      ├─ ahmedabad/norms.json
      ├─ ahmedabad/cost_of_living.json
      └─ ahmedabad/schools.json

2. Python Data Loader (Day 2-3 - 6 hours)
   └─ Create data/seeders/load_ahmedabad.py
   └─ Reads JSON files
   └─ Creates nodes in Neo4j
   └─ Creates hierarchical edges
   └─ Validates no duplicates

3. Conflict Detection (Day 3-4 - 6 hours)
   └─ Create data/seeders/create_conflicts.py
   └─ For each Ahmedabad norm:
      └─ Find corresponding Bangalore norm
      └─ Create CONFLICTS_WITH edge
      └─ Manually set confidence & conflict_level

   └─ Example conflicts to capture:
      ├─ Bargaining (OK in markets Ahmedabad, less common Bangalore)
      ├─ Drinking alcohol (more liberal Bangalore)
      ├─ Dating culture (more progressive Bangalore)
      ├─ Work-life balance (Bangalore startup hustle vs Ahmedabad pace)
      └─ Dress code (Ahmedabad more conservative)

4. Verify Data (Day 4 - 2 hours)
   └─ Query Neo4j to verify:
      ├─ Total nodes > 400
      ├─ No duplicate attractions
      ├─ All conflicts created
      └─ All edges present

PYTHON SCRIPT SNIPPET:
```python
# data/seeders/load_ahmedabad.py

import json
from neo4j import GraphDatabase

class AhmedabadDataLoader:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_pass):
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_pass)
        )

    def load_attractions(self):
        """Load attractions from JSON"""
        with open('data/seeds/ahmedabad/attractions.json') as f:
            attractions = json.load(f)

        with self.driver.session() as session:
            for attr in attractions:
                session.run("""
                    MERGE (a:Attraction {
                        id: $id,
                        name: $name,
                        city: 'ahmedabad',
                        description: $description,
                        coordinates: $coords
                    })
                """, {
                    'id': attr['id'],
                    'name': attr['name'],
                    'description': attr['description'],
                    'coords': attr['coordinates']
                })

    def load_all(self):
        self.load_attractions()
        # ... repeat for restaurants, hotels, etc.

if __name__ == '__main__':
    loader = AhmedabadDataLoader(
        'neo4j://localhost:7687',
        'neo4j',
        'password123'
    )
    loader.load_all()
    print("✓ Ahmedabad data loaded!")
```

---

### WEEK 3: Build Core Agent Logic

#### Goal: Create gap analysis + conflict prioritization

```
DELIVERABLES:
✓ Orchestrator agent (basic Claude integration)
✓ Gap analysis algorithm
✓ Conflict detection queries
✓ /chat/plan endpoint working

TIME: 4 days

TASKS:

1. Claude API Integration (Day 1 - 3 hours)
   └─ Set up Anthropic API credentials
   └─ Create core/orchestrator.py with basic prompt
   └─ Test API calls work

2. Graph Query Engine (Day 1-2 - 5 hours)
   └─ Create:
      ├─ core/gap_analyzer.py
      │  ├─ Function: get_destination_norms(city)
      │  ├─ Function: get_user_known_norms(origin_city)
      │  └─ Function: find_delta(origin, destination)
      │
      └─ core/conflict_detector.py
         ├─ Function: find_high_conflict_norms(origin, dest)
         ├─ Function: prioritize_by_embarrassment()
         └─ Function: rank_learning_path()

3. API Endpoint (Day 2-3 - 4 hours)
   └─ Create api/routes/plan.py
   └─ Endpoint: POST /api/v1/plan

   Request:
   ```json
   {
     "origin_city": "bangalore",
     "destination_city": "ahmedabad",
     "user_type": "professional",
     "time_available_days": 14
   }
   ```

   Response:
   ```json
   {
     "critical_conflicts": [
       {
         "norm": "Bargaining in markets",
         "why_different": "OK in Ahmedabad, less common Bangalore",
         "embarrassment_risk": "high",
         "must_learn": true
       },
       ...
     ],
     "recommended_areas": [
       {
         "name": "Naranpura",
         "vibe": "traditional_Gujarat",
         "similar_to_bangalore": "Not very",
         "rent_range": "₹20-25k"
       },
       ...
     ],
     "quick_setup_checklist": [
       "Find accommodation",
       "Phone/SIM setup",
       ...
     ]
   }
   ```

4. Test with Sample (Day 3-4 - 3 hours)
   └─ Manual test with Bangalore → Ahmedabad
   └─ Verify conflicts detected correctly
   └─ Check API response quality

SAMPLE CYPHER QUERIES:

```cypher
# Query 1: Get all norms in Ahmedabad
MATCH (norm:Norm)-[:NORMAL_IN]->(city:City{name: "Ahmedabad"})
RETURN norm, norm.embarrassment_level
ORDER BY norm.embarrassment_level DESC
LIMIT 15;

# Query 2: Get high-conflict norms (Delhi → Ahmedabad)
MATCH (delhi_norm:Norm)-[:NORMAL_IN]->(delhi:City{name: "Bangalore"})
MATCH (delhi_norm)-[:CONFLICTS_WITH]->(ahmedabad_norm:Norm)
WHERE (ahmedabad_norm)-[:NORMAL_IN]->(ahmedabad:City{name: "Ahmedabad"})
RETURN delhi_norm.title, ahmedabad_norm.title,
       ahmedabad_norm.embarrassment_level,
       ahmedabad_norm.conflict_type
ORDER BY ahmedabad_norm.embarrassment_level DESC
LIMIT 10;

# Query 3: Find similar areas
MATCH (src_area:Area{city: "bangalore", name: "Indiranagar"})
MATCH (dest_area:Area{city: "ahmedabad"})
WHERE vector_similarity(src_area.vibe_vector, dest_area.vibe_vector) > 0.7
RETURN dest_area, similarity_score
ORDER BY similarity_score DESC;
```

---

### WEEK 4: Build User Personalization

#### Goal: Track user learning + create personalized recommendations

```
DELIVERABLES:
✓ PostgreSQL user model working
✓ Learning state tracking (what user has seen)
✓ Retention scoring
✓ Personalized recommendation endpoint
✓ Spaced repetition scheduler (basic)

TIME: 4 days

TASKS:

1. User Model Setup (Day 1-2 - 5 hours)
   └─ Create data/models.py

   Models:
   ```python
   class User:
       user_id: UUID
       origin_city: str
       destination_city: str
       knowledge_state: JSONB  # {norm_id: {seen, retention_score}}
       preferences: JSONB

   class UserInteraction:
       user_id: UUID
       node_id: str
       interaction_type: Enum(viewed, completed, struggled)
       retention_score: float (0-1)
       timestamp: datetime
   ```

2. Learning State Tracker (Day 2 - 3 hours)
   └─ Create core/personalization.py
   └─ Function: track_node_viewed(user_id, node_id)
   └─ Function: update_retention_score(user_id, node_id, score)
   └─ Function: get_user_delta(user_id)

3. Personalization Endpoint (Day 3 - 3 hours)
   └─ POST /api/v1/personalize

   Input:
   ```json
   {
     "user_id": "user_123",
     "query": "I'm a vegetarian. What should I know?"
   }
   ```

   Output:
   ```json
   {
     "top_3_recommendations": [
       {
         "node": "vegetarian_culture_norm",
         "reason": "29x vegetarian population, different from Bangalore",
         "action": "Learn about this"
       },
       ...
     ]
   }
   ```

4. Spaced Repetition Setup (Day 4 - 3 hours)
   └─ Create core/spaced_repetition.py
   └─ Simple SM-2 algorithm implementation
   └─ Function: get_next_review_date(user_id, node_id)
   └─ Background job (can be manual for MVP)

---

### WEEK 5-6: Build Frontend + Polish

#### Goal: Simple web UI + end-to-end testing

```
DELIVERABLES:
✓ Simple React/HTML frontend
✓ Chat interface working
✓ Plan display working
✓ User dashboard showing progress
✓ End-to-end tests passing

TIME: 2 weeks (but can be simpler UI)

MINIMAL FRONTEND:
- /dashboard - Shows user's current plan
- /chat - Chat interface with bot
- /explore - Browse Ahmedabad info
- /compare - Side-by-side Bangalore vs Ahmedabad

TECH:
- React + TypeScript (or simple HTML if time-constrained)
- Tailwind CSS for styling
- Fetch API for backend calls
```

---

### WEEK 7-8: Beta Testing + Launch

#### Goal: User feedback + iterate

```
DELIVERABLES:
✓ 50 beta users ($INVITE)
✓ Collect feedback
✓ Fix critical bugs
✓ Launch MVP

TESTING FOCUS:
- Does plan actually help first-time arrivals?
- Are norms accurate?
- Is UI intuitive?
- Missing features?
```

---

## IMMEDIATE ACTION: START THIS WEEK

### What to Build First (Pick One):

**Option A: Data Collection (Fastest to impact)**
```
1. Set up Google Maps API
2. Create script to fetch Ahmedabad attractions
3. Export to JSON
4. Load into Neo4j

   Status: You have real data in graph in 2 days
   Why: Everything depends on good data
```

**Option B: Backend Infrastructure (Most structured)**
```
1. Docker compose setup (Neo4j + PostgreSQL)
2. Python FastAPI skeleton
3. First Neo4j query (get city info)

   Status: Working API in 1 day
   Why: Unblocks rest of team
```

**Option C: Conflict Data Curation (Most creative)**
```
1. Create Google Sheet: "Bangalore vs Ahmedabad Norms"
2. Brain-dump 20 key cultural differences
3. Score embarrassment risk for each
4. Convert to Cypher creation script

   Status: Real conflict data in graph in 2 days
   Why: This is the unique value prop
```

---

## RECOMMENDED EXECUTION ORDER

```
PARALLEL PATH:

Week 1 (3 people):
├─ Person A: Docker setup + Neo4j schema (Option B)
├─ Person B: Google Maps API data collection (Option A)
└─ Person C: Conflict data curation (Option C)

Week 2:
├─ Person A: Build data loader script
├─ Person B: Load data into Neo4j
└─ Person C: Create agent prompts

Week 3:
├─ Person A: Build orchestrator + gap analysis
├─ Person B: Build conflict detection queries
└─ Person C: Write Cypher query library

Week 4:
├─ Person A: User model + personalization
├─ Person B: Frontend (chat interface)
└─ Person C: Testing + bug fixes

Weeks 5-8:
├─ All: Polish + beta testing
```

---

## SUCCESS METRICS (MVP)

```
✓ Can a new user type "Bangalore → Ahmedabad" and get top 10 conflicts?
✓ Are conflicts accurate (validate with 20 people)?
✓ Can system rank conflicts by embarrassment risk?
✓ Can system recommend similar areas?
✓ UI takes <2s to load plan?
✓ At least 2 of 4 personas happy with plan?
```

---

## EPILOGUE: Beyond MVP

Once MVP works with 1 route, scaling is:

1. **Add Gwalior** (1 week)
   - Collect same data
   - Auto-detect conflicts (feature vectors)
   - Done

2. **Add Traveler Support** (1 week)
   - Same data, different prioritization
   - Safety by time of day
   - Language focus

3. **Mobile App** (3 weeks)
   - React Native wrapping same APIs
   - Offline capabilities
   - Push notifications

4. **Real-Time Data** (2 weeks)
   - Weather API integration
   - Events API
   - Safety alerts

---

## CONCLUSION

You have everything you need. The docs are complete. The personas are clear. The build path is concrete.

**Start today with Option A, B, or C above. Pick one. Spend 4 hours. Get to working proof-of-concept by EOD.**

The rest is just iteration.

Let's go. 🚀

---

**Ready to start building?**

Pick your path above and reply with:
1. Which option (A/B/C)?
2. Which person would tackle it first?
3. What's your first blockaer?

I'll help you unblock immediately.



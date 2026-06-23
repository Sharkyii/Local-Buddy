"""
Data Models for Local Buddy
Defines all data structures for ingestion
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import json


class NormType(Enum):
    """Types of norms in a city"""
    BARGAINING = "bargaining"
    DRESS_CODE = "dress_code"
    WORK_CULTURE = "work_culture"
    SOCIAL = "social"
    FOOD = "food"
    TRANSPORT = "transport"
    GENDER_SPECIFIC = "gender_specific"
    GENERAL = "general"


class SafetyLevel(Enum):
    """Safety ratings for areas"""
    VERY_SAFE = "very_safe"
    SAFE = "safe"
    MODERATE = "moderate"
    UNSAFE = "unsafe"


class PlaceCategory(Enum):
    """Categories for attractions/places"""
    HISTORICAL = "historical"
    RELIGIOUS = "religious"
    MUSEUM = "museum"
    PARK = "park"
    GARDEN = "garden"
    LAKE = "lake"
    RIVER = "river"
    DAM = "dam"
    VIEWPOINT = "viewpoint"
    WILDLIFE = "wildlife"
    BEACH = "beach"
    WATERFALL = "waterfall"
    MARKET = "market"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"  # cinemas, theatres, theme/water parks, amusement arcades
    NIGHTLIFE = "nightlife"  # nightclubs
    POOL = "pool"  # swimming pools
    FOOD = "food"
    EDUCATIONAL = "educational"
    NATURE = "nature"
    HEALTHCARE = "healthcare"  # hospitals, clinics, pharmacies
    FINANCE = "finance"  # ATMs, banks
    TRANSPORT = "transport"  # bus stops/stations, railway stations
    FITNESS = "fitness"  # gyms/fitness centres
    LANDMARK = "landmark"  # public art/sculptures/generic attractions — honest catch-all,
                           # NOT a synonym for "entertainment" (cinemas/theme parks etc.)


# Buckets the fine-grained PlaceCategory values into a handful of clean
# top-level groups for display (map legends, agent summaries) without losing
# the precise category used for filtering. Pure lookup, not stored on nodes —
# computed at read time in Repository so it can't drift out of sync.
CATEGORY_GROUPS: Dict[str, str] = {
    "historical": "Heritage & Culture",
    "religious": "Heritage & Culture",
    "museum": "Heritage & Culture",
    "landmark": "Heritage & Culture",
    "park": "Nature & Outdoors",
    "garden": "Nature & Outdoors",
    "lake": "Nature & Outdoors",
    "river": "Nature & Outdoors",
    "dam": "Nature & Outdoors",
    "viewpoint": "Nature & Outdoors",
    "wildlife": "Nature & Outdoors",
    "beach": "Nature & Outdoors",
    "waterfall": "Nature & Outdoors",
    "nature": "Nature & Outdoors",
    "market": "Shopping & Leisure",
    "shopping": "Shopping & Leisure",
    "entertainment": "Shopping & Leisure",
    "nightlife": "Shopping & Leisure",
    "pool": "Shopping & Leisure",
    "educational": "Education",
    "healthcare": "Services & Utilities",
    "finance": "Services & Utilities",
    "transport": "Services & Utilities",
    "fitness": "Services & Utilities",
}


def category_group(category: Optional[str]) -> str:
    return CATEGORY_GROUPS.get(category, "Other")


@dataclass
class Coordinates:
    """GPS coordinates"""
    lat: float
    lng: float

    def to_dict(self):
        return {"lat": self.lat, "lng": self.lng}


@dataclass
class TimingHours:
    """Operating hours"""
    opens: str  # HH:MM format
    closes: str  # HH:MM format
    closed_days: List[str] = None  # ["Monday", "Tuesday"]
    break_time: Optional[Dict[str, str]] = None  # {"start": "13:00", "end": "14:00"}

    def to_dict(self):
        return {
            "opens": self.opens,
            "closes": self.closes,
            "closed_days": self.closed_days or [],
            "break_time": self.break_time
        }


@dataclass
class City:
    """City node in knowledge graph"""
    id: str  # "ahmedabad", "bangalore", "gwalior"
    name: str
    state: str
    country: str = "India"
    population: int = 0
    primary_language: str = "Hindi"
    secondary_languages: List[str] = None
    timezone: str = "IST"
    currency: str = "INR"
    climate_type: str = ""
    urban_density: str = "urban"
    culture_vibe: str = ""
    cost_of_living_index: float = 100.0  # Bangalore = 100
    safety_index: float = 7.0  # 1-10
    infrastructure_score: float = 7.0  # 1-10
    description: str = ""
    data_source: str = "manual"
    created_at: str = None

    def __post_init__(self):
        if self.secondary_languages is None:
            self.secondary_languages = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)


@dataclass
class Area:
    """Area/neighborhood within a city"""
    id: str  # "bandra_mumbai"
    name: str
    city: str  # city_id
    locality_type: str  # "residential", "commercial", "trendy", "traditional"
    coordinates: Coordinates
    population: int = 0
    average_rent_1bhk: int = 0  # in INR
    demographics: Dict[str, Any] = None
    lifestyle_tags: List[str] = None  # ["artsy", "expat_friendly", "nightlife"]
    safety_level: SafetyLevel = SafetyLevel.SAFE
    public_transport_score: int = 5  # 1-10
    walkability_score: int = 5  # 1-10
    cultural_vibe: str = ""
    area_reputation: str = ""
    notable_for: List[str] = None
    data_source: str = "manual"
    created_at: str = None

    def __post_init__(self):
        if isinstance(self.safety_level, str):
            self.safety_level = SafetyLevel(self.safety_level)
        if self.demographics is None:
            self.demographics = {}
        if self.lifestyle_tags is None:
            self.lifestyle_tags = []
        if self.notable_for is None:
            self.notable_for = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        data = asdict(self)
        data['coordinates'] = self.coordinates.to_dict()
        data['safety_level'] = self.safety_level.value
        return data


@dataclass
class Place:
    """Attraction/landmark"""
    id: str  # "taj_gateway_mumbai"
    name: str
    city: str
    area: str
    place_type: str  # "monument", "museum", "temple", etc.
    category: PlaceCategory
    significance: str  # "national_symbol", "local", "historical"
    coordinates: Coordinates
    description: str = ""
    history: str = ""
    visiting_hours: TimingHours = None
    entry_fee: Dict[str, int] = None  # {"local": 0, "foreign": 600, "child": 0}
    duration_hours: float = 1.0
    best_visiting_time: Dict[str, str] = None  # {"season": "nov_to_feb", "time_of_day": "sunset"}
    crowd_levels: Dict[str, str] = None  # {"morning": "low", "afternoon": "high"}
    accessibility: Dict[str, bool] = None
    photography_allowed: bool = True
    distance_from_center_km: float = 0.0
    must_visit: bool = False
    data_source: str = "google_maps"
    google_places_id: str = ""
    google_rating: float = 0.0
    google_reviews: int = 0
    created_at: str = None

    def __post_init__(self):
        if isinstance(self.category, str):
            self.category = PlaceCategory(self.category)
        if self.visiting_hours is None:
            self.visiting_hours = TimingHours(opens="09:00", closes="18:00")
        if self.entry_fee is None:
            self.entry_fee = {"local": 0, "foreign": 0}
        if self.best_visiting_time is None:
            self.best_visiting_time = {}
        if self.crowd_levels is None:
            self.crowd_levels = {}
        if self.accessibility is None:
            self.accessibility = {"wheelchair": False, "parking": False}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        data = asdict(self)
        data['coordinates'] = self.coordinates.to_dict()
        data['category'] = self.category.value
        data['visiting_hours'] = self.visiting_hours.to_dict()
        return data


@dataclass
class Restaurant:
    """Food establishment"""
    id: str
    name: str
    city: str
    area: str
    coordinates: Coordinates
    cuisine_types: List[str]
    specialty_dishes: List[str] = None
    price_range: str = "moderate"  # budget, moderate, expensive
    average_cost_per_person: int = 0
    vegetarian_options: bool = False
    vegan_options: bool = False
    allergen_info: Dict[str, bool] = None  # {"nuts": True, "dairy": False}
    operating_hours: TimingHours = None
    google_rating: float = 0.0
    zomato_rating: float = 0.0
    ambiance: str = ""
    reservation_needed: bool = False
    data_source: str = "zomato"
    google_places_id: str = ""
    created_at: str = None

    def __post_init__(self):
        if self.specialty_dishes is None:
            self.specialty_dishes = []
        if self.allergen_info is None:
            self.allergen_info = {}
        if self.operating_hours is None:
            self.operating_hours = TimingHours(opens="11:00", closes="23:00")
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        data = asdict(self)
        data['coordinates'] = self.coordinates.to_dict()
        data['operating_hours'] = self.operating_hours.to_dict()
        return data


@dataclass
class Hotel:
    """Accommodation"""
    id: str
    name: str
    city: str
    area: str
    coordinates: Coordinates
    stars: int  # 1-5
    hotel_type: str = "hotel"  # OSM tourism tag: hotel/resort/hostel/guest_house/motel
    price_per_night: Dict[str, int] = None  # {"economy": 1000, "standard": 2000}
    amenities: List[str] = None
    specialties: List[str] = None
    accessibility: Dict[str, bool] = None
    google_rating: float = 0.0
    check_in_time: str = "14:00"
    check_out_time: str = "11:00"
    data_source: str = "google_maps"
    google_places_id: str = ""
    created_at: str = None

    def __post_init__(self):
        if self.price_per_night is None:
            self.price_per_night = {}
        if self.amenities is None:
            self.amenities = []
        if self.specialties is None:
            self.specialties = []
        if self.accessibility is None:
            self.accessibility = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        data = asdict(self)
        data['coordinates'] = self.coordinates.to_dict()
        return data


@dataclass
class Norm:
    """Cultural norm/behavior expected in city"""
    id: str
    city: str
    title: str
    category: NormType
    description: str = ""
    context: Dict[str, Any] = None  # where, when, with_whom
    dos: List[str] = None
    donts: List[str] = None
    embarrassment_risk: int = 5  # 1-10
    prevalence: str = "common"  # common, occasional, rare
    acceptability: str = "acceptable"  # acceptable, neutral, unacceptable
    gender_specific: bool = False
    relevance_for_travelers: str = "medium"  # low, medium, high
    data_source: str = "manual"
    confidence_score: float = 0.8  # 0-1
    created_at: str = None

    def __post_init__(self):
        if isinstance(self.category, str):
            self.category = NormType(self.category)
        if self.context is None:
            self.context = {}
        if self.dos is None:
            self.dos = []
        if self.donts is None:
            self.donts = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        data = asdict(self)
        data['category'] = self.category.value
        return data


@dataclass
class School:
    """Educational institution"""
    id: str
    name: str
    city: str
    area: str
    coordinates: Coordinates
    school_type: str  # "government", "private", "international"
    curriculum: str  # "CISCE", "CBSE", "IB", "Gujarati"
    annual_fees: int = 0  # in INR
    grades_offered: List[int] = None
    safety_rating: float = 0.0
    parent_rating: float = 0.0
    student_faculty_ratio: str = ""
    distance_from_city_center_km: float = 0.0
    data_source: str = "manual"
    created_at: str = None

    def __post_init__(self):
        if self.grades_offered is None:
            self.grades_offered = list(range(1, 13))
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        data = asdict(self)
        data['coordinates'] = self.coordinates.to_dict()
        return data


@dataclass
class CostOfLiving:
    """Cost metrics for a city"""
    id: str
    city: str
    category: str  # "accommodation", "food", "transport"
    item: str  # "1BHK apartment", "meal at restaurant"
    price_range: Dict[str, int] = None  # {"min": 15000, "max": 35000, "avg": 22000}
    neighborhood_breakdown: Dict[str, Dict] = None  # {area: {price, vibe}}
    compared_to_city: str = ""  # for parity calculation
    parity_ratio: float = 1.0  # how much cheaper/expensive
    data_source: str = "manual"
    created_at: str = None

    def __post_init__(self):
        if self.price_range is None:
            self.price_range = {}
        if self.neighborhood_breakdown is None:
            self.neighborhood_breakdown = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)


# Helper function to convert between dict and model objects
def serialize_model(obj):
    """Convert dataclass to JSON-serializable dict"""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    return asdict(obj)


def to_json(obj) -> str:
    """Convert model to JSON string"""
    return json.dumps(serialize_model(obj), indent=2)

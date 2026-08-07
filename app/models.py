from typing import Literal

from pydantic import BaseModel, Field


Preference = Literal["photo", "food", "culture", "shopping", "nature"]
CrowdTolerance = Literal["low", "medium", "high"]
Language = Literal["en", "ko"]
CrowdLevel = Literal["relaxed", "normal", "busy", "crowded"]
FoodStopMode = Literal["none", "optional", "required"]
FoodPreference = Literal["quick", "meal", "cafe", "any"]
PlaceType = Literal["attraction", "restaurant", "cafe"]
PlaceSource = Literal["curated", "tourapi", "kakao-local"]


class Place(BaseModel):
    id: str
    name_en: str
    name_ko: str
    description_en: str
    description_ko: str
    latitude: float
    longitude: float
    duration_minutes: int
    tags: list[Preference]
    hotspot: str
    indoor: bool = False
    open_24h: bool = False
    opening_hour: int | None = None
    closing_hour: int | None = None
    closed_weekdays: list[int] = Field(default_factory=list)
    opening_note_en: str = "Check current opening hours"
    opening_note_ko: str = "방문 전 운영시간 확인"
    image_url: str | None = None
    place_type: PlaceType = "attraction"
    data_source: PlaceSource = "curated"
    category_name: str | None = None
    address: str | None = None
    distance_meters: int | None = Field(default=None, ge=0)
    external_url: str | None = None
    minimum_duration_minutes: int | None = Field(default=None, ge=10, le=120)


class CrowdSnapshot(BaseModel):
    hotspot: str
    level: CrowdLevel
    message: str
    updated_at: str
    source: Literal["seoul-realtime", "estimated"]


class RecommendationRequest(BaseModel):
    latitude: float = Field(ge=37.0, le=38.0)
    longitude: float = Field(ge=126.0, le=128.0)
    available_minutes: int = Field(ge=60, le=240)
    preferences: list[Preference] = Field(min_length=1, max_length=5)
    crowd_tolerance: CrowdTolerance = "low"
    language: Language = "en"
    food_stop: FoodStopMode = "none"
    food_preference: FoodPreference = "any"


class CourseStop(BaseModel):
    order: int
    place: Place
    crowd: CrowdSnapshot
    travel_from_previous_minutes: int
    visit_minutes: int
    arrival_minute: int
    leave_minute: int


class TimeBudget(BaseModel):
    travel_minutes: int
    visit_minutes: int
    activity_minutes: int = 0
    food_minutes: int = 0
    buffer_minutes: int
    unused_minutes: int
    total_minutes: int


class Course(BaseModel):
    id: str
    badge: str
    title: str
    summary: str
    score: int
    crowd_level: CrowdLevel
    time_budget: TimeBudget
    stops: list[CourseStop]
    route: list[list[float]]


class DataSourceStatus(BaseModel):
    tour_api: Literal["live", "demo"]
    seoul_city_data: Literal["live", "estimated"]
    routing: Literal["walking-estimate"]
    kakao_local: Literal["live", "off", "error"] = "off"
    kakao_local_detail: str = "not-configured"


class RecommendationResponse(BaseModel):
    courses: list[Course]
    generated_at: str
    origin: list[float]
    data_sources: DataSourceStatus
    notice: str

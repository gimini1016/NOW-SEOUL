import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.data import PLACES, PRESET_ORIGINS
from app.engine import candidate_places, recommend_courses
from app.models import DataSourceStatus, RecommendationRequest, RecommendationResponse
from app.services import SeoulCrowdService, TourAPIService


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
SEOUL_TZ = ZoneInfo("Asia/Seoul")

app = FastAPI(
    title="NOW SEOUL API",
    description="Time-boxed, crowd-aware micro itinerary recommendations for Seoul.",
    version="0.1.0",
)

allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

crowd_service = SeoulCrowdService()
tour_service = TourAPIService()


@app.get("/", include_in_schema=False)
def homepage() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "NOW SEOUL"}


@app.get("/api/config", tags=["system"])
def config() -> dict:
    return {
        "presets": PRESET_ORIGINS,
        "preferences": ["photo", "food", "culture", "shopping", "nature"],
        "data_sources": DataSourceStatus(
            tour_api="live" if tour_service.is_live else "demo",
            seoul_city_data="live" if crowd_service.is_live else "estimated",
            routing="walking-estimate",
        ),
    }


@app.get("/api/places", tags=["places"])
def places() -> list:
    return PLACES


@app.post("/api/recommend", response_model=RecommendationResponse, tags=["recommendations"])
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    now = datetime.now(SEOUL_TZ)
    enriched_places = tour_service.enrich(PLACES, request.latitude, request.longitude)
    candidates = candidate_places(request, enriched_places, now)

    if not candidates:
        raise HTTPException(status_code=422, detail="No open places were available for this request.")

    hotspots = {place.hotspot for place in candidates}
    crowds = crowd_service.get_many(hotspots, now)
    courses = recommend_courses(request, candidates, crowds)

    if not courses:
        raise HTTPException(
            status_code=422,
            detail="No course fits this time budget. Try a nearby starting point or more time.",
        )

    language_notice = {
        "en": "Walking times and opening hours are estimates. Check official information before visiting.",
        "ko": "도보시간과 운영시간은 추정치입니다. 방문 전 공식 정보를 확인해 주세요.",
    }
    return RecommendationResponse(
        courses=courses,
        generated_at=now.isoformat(),
        origin=[request.latitude, request.longitude],
        data_sources=DataSourceStatus(
            tour_api="live" if tour_service.is_live else "demo",
            seoul_city_data="live" if crowd_service.is_live else "estimated",
            routing="walking-estimate",
        ),
        notice=language_notice[request.language],
    )

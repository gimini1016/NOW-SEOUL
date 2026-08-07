from datetime import datetime
from zoneinfo import ZoneInfo

from app.data import PLACES
from app.engine import candidate_places, haversine_km, recommend_courses, walking_minutes
from app.models import CrowdSnapshot, RecommendationRequest


SEOUL_TZ = ZoneInfo("Asia/Seoul")


def crowd_snapshots(places):
    return {
        place.hotspot: CrowdSnapshot(
            hotspot=place.hotspot,
            level="normal",
            message="test",
            updated_at="2026-08-07T12:00:00+09:00",
            source="estimated",
        )
        for place in places
    }


def test_distance_and_walking_time_are_positive():
    distance = haversine_km(37.5636, 126.9869, 37.5658, 126.9751)
    minutes = walking_minutes(37.5636, 126.9869, 37.5658, 126.9751)

    assert 0.8 < distance < 1.3
    assert minutes >= 10


def test_recommendations_fit_two_hour_budget():
    request = RecommendationRequest(
        latitude=37.5636,
        longitude=126.9869,
        available_minutes=120,
        preferences=["photo", "culture"],
        crowd_tolerance="low",
        language="en",
    )
    now = datetime(2026, 8, 7, 12, 0, tzinfo=SEOUL_TZ)
    candidates = candidate_places(request, PLACES, now)
    courses = recommend_courses(request, candidates, crowd_snapshots(candidates))

    assert len(courses) == 3
    assert all(course.time_budget.total_minutes <= 120 for course in courses)
    assert all(course.time_budget.buffer_minutes >= 10 for course in courses)
    assert all(course.stops for course in courses)


def test_ninety_minute_request_is_supported():
    request = RecommendationRequest(
        latitude=37.5759,
        longitude=126.9768,
        available_minutes=90,
        preferences=["culture"],
        crowd_tolerance="medium",
        language="ko",
    )
    now = datetime(2026, 8, 7, 11, 0, tzinfo=SEOUL_TZ)
    candidates = candidate_places(request, PLACES, now)
    courses = recommend_courses(request, candidates, crowd_snapshots(candidates))

    assert courses
    assert all(course.time_budget.total_minutes <= 90 for course in courses)
    assert courses[0].title


def test_one_hour_hongdae_request_still_returns_top_three():
    request = RecommendationRequest(
        latitude=37.5572,
        longitude=126.9246,
        available_minutes=60,
        preferences=["food", "shopping"],
        crowd_tolerance="high",
        language="en",
    )
    now = datetime(2026, 8, 7, 12, 0, tzinfo=SEOUL_TZ)
    candidates = candidate_places(request, PLACES, now)
    courses = recommend_courses(request, candidates, crowd_snapshots(candidates))

    assert len(courses) == 3
    assert all(course.time_budget.total_minutes <= 60 for course in courses)
    assert all(stop.visit_minutes >= 20 for course in courses for stop in course.stops)

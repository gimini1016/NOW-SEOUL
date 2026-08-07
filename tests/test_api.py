from fastapi.testclient import TestClient

from app.main import app, kakao_service
from app.models import Place


client = TestClient(app)


def test_health_and_homepage():
    health = client.get("/api/health")
    homepage = client.get("/")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert homepage.status_code == 200
    assert "NOW SEOUL" in homepage.text
    assert "data-food-mode" in homepage.text


def test_config_exposes_demo_mode_without_keys():
    response = client.get("/api/config")

    assert response.status_code == 200
    assert "presets" in response.json()
    assert response.json()["data_sources"]["routing"] == "walking-estimate"


def test_recommend_endpoint_returns_three_time_safe_courses():
    response = client.post(
        "/api/recommend",
        json={
            "latitude": 37.5636,
            "longitude": 126.9869,
            "available_minutes": 120,
            "preferences": ["photo", "culture"],
            "crowd_tolerance": "low",
            "language": "en",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["courses"]) == 3
    assert all(course["time_budget"]["total_minutes"] <= 120 for course in payload["courses"])
    assert payload["origin"] == [37.5636, 126.9869]


def test_request_validation_rejects_too_little_time():
    response = client.post(
        "/api/recommend",
        json={
            "latitude": 37.5636,
            "longitude": 126.9869,
            "available_minutes": 30,
            "preferences": ["photo"],
        },
    )

    assert response.status_code == 422


def test_required_food_mode_explains_missing_local_api_data():
    response = client.post(
        "/api/recommend",
        json={
            "latitude": 37.5636,
            "longitude": 126.9869,
            "available_minutes": 120,
            "preferences": ["culture"],
            "food_stop": "required",
            "food_preference": "meal",
            "language": "ko",
        },
    )

    assert response.status_code == 422
    assert "음식점" in response.json()["detail"]


def test_optional_food_request_includes_kakao_place_and_time_budget(monkeypatch):
    restaurant = Place(
        id="kakao-api-test",
        name_en="API Test Restaurant",
        name_ko="API 테스트 식당",
        description_en="Test restaurant",
        description_ko="테스트 음식점",
        latitude=37.5642,
        longitude=126.9848,
        duration_minutes=55,
        minimum_duration_minutes=45,
        tags=["food"],
        hotspot="명동 관광특구",
        indoor=True,
        place_type="restaurant",
        data_source="kakao-local",
        address="서울 중구 테스트로 1",
        distance_meters=180,
        external_url="https://place.map.kakao.com/123",
    )
    monkeypatch.setattr(kakao_service, "search_nearby", lambda *args, **kwargs: [restaurant])

    response = client.post(
        "/api/recommend",
        json={
            "latitude": 37.5636,
            "longitude": 126.9869,
            "available_minutes": 120,
            "preferences": ["photo", "culture"],
            "food_stop": "optional",
            "food_preference": "meal",
            "language": "ko",
        },
    )

    assert response.status_code == 200, response.text
    courses = response.json()["courses"]
    food_courses = [
        course
        for course in courses
        if any(stop["place"]["data_source"] == "kakao-local" for stop in course["stops"])
    ]
    assert len(food_courses) == 1
    assert food_courses[0]["time_budget"]["food_minutes"] >= 45
    assert food_courses[0]["time_budget"]["activity_minutes"] >= 0

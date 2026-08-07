from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_and_homepage():
    health = client.get("/api/health")
    homepage = client.get("/")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert homepage.status_code == 200
    assert "NOW SEOUL" in homepage.text


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

from app.data import PLACES
from app.services import KakaoLocalService


def test_kakao_documents_are_converted_to_time_aware_places():
    service = KakaoLocalService()
    documents = [
        {
            "id": "98765",
            "place_name": "서울 테스트 식당",
            "category_name": "음식점 > 한식 > 국수",
            "road_address_name": "서울 중구 세종대로 1",
            "address_name": "서울 중구 테스트동 1",
            "x": "126.9848",
            "y": "37.5642",
            "distance": "220",
            "place_url": "https://place.map.kakao.com/98765",
        }
    ]

    places = service._parse_documents(documents, "FD6", "quick", PLACES)

    assert len(places) == 1
    place = places[0]
    assert place.name_ko == "서울 테스트 식당"
    assert place.place_type == "restaurant"
    assert place.data_source == "kakao-local"
    assert place.minimum_duration_minutes == 25
    assert place.distance_meters == 220
    assert place.external_url == "https://place.map.kakao.com/98765"


def test_kakao_cafe_receives_cafe_duration():
    service = KakaoLocalService()
    documents = [
        {
            "id": "cafe-1",
            "place_name": "서울 테스트 카페",
            "category_name": "음식점 > 카페",
            "x": "126.9850",
            "y": "37.5640",
            "distance": "150",
            "place_url": "https://place.map.kakao.com/cafe-1",
        }
    ]

    place = service._parse_documents(documents, "CE7", "cafe", PLACES)[0]

    assert place.place_type == "cafe"
    assert place.duration_minutes == 40
    assert place.minimum_duration_minutes == 30


def test_meal_preference_filters_dessert_and_keeps_full_meal_duration():
    service = KakaoLocalService()
    documents = [
        {
            "id": "dessert-1",
            "place_name": "테스트 젤라또",
            "category_name": "음식점 > 간식 > 아이스크림",
            "x": "126.9850",
            "y": "37.5640",
            "distance": "20",
        },
        {
            "id": "meal-1",
            "place_name": "테스트 한식당",
            "category_name": "음식점 > 한식",
            "x": "126.9848",
            "y": "37.5642",
            "distance": "80",
        },
    ]

    places = service._parse_documents(documents, "FD6", "meal", PLACES)

    assert [place.name_ko for place in places] == ["테스트 한식당"]
    assert places[0].duration_minutes == 55
    assert places[0].minimum_duration_minutes == 45


def test_kakao_http_errors_are_reported_without_exposing_credentials():
    reason = KakaoLocalService._kakao_error_reason
    assert reason(401, None) == "authentication-error"
    assert reason(403, -3) == "feature-not-enabled"
    assert reason(403, -5) == "permission-required"
    assert reason(403, -12) == "app-suspended"
    assert reason(401, -401) == "invalid-key-or-ip"
    assert reason(429, None) == "quota-error"
    assert reason(500, None) == "upstream-http-500"

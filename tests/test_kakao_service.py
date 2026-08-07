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

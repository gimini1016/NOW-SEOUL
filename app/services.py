import json
import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models import CrowdSnapshot, FoodPreference, Place


class TTLCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, object]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> object | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            created_at, value = item
            if time.monotonic() - created_at > self.ttl_seconds:
                self._items.pop(key, None)
                return None
            return value

    def set(self, key: str, value: object) -> None:
        with self._lock:
            self._items[key] = (time.monotonic(), value)


def _find_dict_with_key(value: object, target_key: str) -> dict | None:
    if isinstance(value, dict):
        if target_key in value:
            return value
        for child in value.values():
            found = _find_dict_with_key(child, target_key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_dict_with_key(child, target_key)
            if found is not None:
                return found
    return None


class SeoulCrowdService:
    LEVEL_MAP = {
        "여유": "relaxed",
        "보통": "normal",
        "약간 붐빔": "busy",
        "붐빔": "crowded",
        "relaxed": "relaxed",
        "normal": "normal",
        "busy": "busy",
        "crowded": "crowded",
    }

    ESTIMATED_BASE = {
        "광화문·덕수궁": 1,
        "명동 관광특구": 2,
        "남산공원": 1,
        "종로·청계 관광특구": 1,
        "경복궁": 2,
        "북촌한옥마을": 2,
        "인사동·익선동": 2,
        "창덕궁·종묘": 1,
        "동대문 관광특구": 2,
        "홍대 관광특구": 2,
        "망원한강공원": 1,
        "월드컵공원": 0,
        "여의도한강공원": 1,
        "강남 MICE 관광특구": 2,
        "가로수길": 1,
        "반포한강공원": 1,
    }

    def __init__(self) -> None:
        self.api_key = os.getenv("SEOUL_OPEN_DATA_KEY", "").strip()
        self.cache = TTLCache(ttl_seconds=300)

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    def get_many(self, hotspots: set[str], now: datetime) -> dict[str, CrowdSnapshot]:
        if not hotspots:
            return {}
        if not self.is_live:
            return {hotspot: self._estimated(hotspot, now) for hotspot in hotspots}

        with ThreadPoolExecutor(max_workers=min(6, len(hotspots))) as executor:
            snapshots = executor.map(lambda hotspot: self.get(hotspot, now), sorted(hotspots))
        return {snapshot.hotspot: snapshot for snapshot in snapshots}

    def get(self, hotspot: str, now: datetime) -> CrowdSnapshot:
        cached = self.cache.get(hotspot)
        if isinstance(cached, CrowdSnapshot):
            return cached

        try:
            snapshot = self._fetch_live(hotspot, now)
        except (OSError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
            snapshot = self._estimated(hotspot, now)

        self.cache.set(hotspot, snapshot)
        return snapshot

    def _fetch_live(self, hotspot: str, now: datetime) -> CrowdSnapshot:
        encoded_hotspot = quote(hotspot, safe="")
        url = (
            "http://openapi.seoul.go.kr:8088/"
            f"{self.api_key}/json/citydata_ppltn/1/5/{encoded_hotspot}"
        )
        request = Request(url, headers={"User-Agent": "NOW-SEOUL/1.0"})
        with urlopen(request, timeout=4) as response:
            payload = json.load(response)

        row = _find_dict_with_key(payload, "AREA_CONGEST_LVL")
        if row is None:
            raise ValueError("Seoul city data did not contain congestion fields")

        raw_level = str(row["AREA_CONGEST_LVL"]).strip().lower()
        level = self.LEVEL_MAP.get(raw_level)
        if level is None:
            raise ValueError(f"Unknown congestion level: {raw_level}")

        return CrowdSnapshot(
            hotspot=hotspot,
            level=level,
            message=str(row.get("AREA_CONGEST_MSG") or "Live Seoul crowd data"),
            updated_at=str(row.get("PPLTN_TIME") or now.isoformat()),
            source="seoul-realtime",
        )

    def _estimated(self, hotspot: str, now: datetime) -> CrowdSnapshot:
        level_names = ["relaxed", "normal", "busy", "crowded"]
        base = self.ESTIMATED_BASE.get(hotspot, 1)
        if now.hour in {12, 13, 18, 19, 20}:
            base += 1
        elif now.hour < 9:
            base -= 1
        level = level_names[max(0, min(base, 3))]
        return CrowdSnapshot(
            hotspot=hotspot,
            level=level,
            message="Estimated crowd level — add a Seoul Open Data key for live data.",
            updated_at=now.isoformat(),
            source="estimated",
        )


class TourAPIService:
    def __init__(self) -> None:
        self.api_key = os.getenv("TOUR_API_KEY", "").strip()
        self.cache = TTLCache(ttl_seconds=3600)

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    def enrich(self, places: list[Place], latitude: float, longitude: float) -> list[Place]:
        if not self.is_live:
            return places

        cache_key = f"{latitude:.2f}:{longitude:.2f}"
        cached = self.cache.get(cache_key)
        if isinstance(cached, dict):
            tour_items = cached
        else:
            try:
                tour_items = self._fetch_nearby(latitude, longitude)
                self.cache.set(cache_key, tour_items)
            except (OSError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
                return places

        enriched = []
        for place in places:
            candidates = [place.name_ko.replace(" ", ""), place.name_en.lower().replace(" ", "")]
            match = next((tour_items[key] for key in candidates if key in tour_items), None)
            if match is None:
                enriched.append(place)
                continue
            enriched.append(place.model_copy(update={"image_url": match.get("firstimage") or place.image_url}))
        return enriched

    def _fetch_nearby(self, latitude: float, longitude: float) -> dict[str, dict]:
        query = urlencode(
            {
                "serviceKey": self.api_key,
                "MobileOS": "ETC",
                "MobileApp": "NOWSEOUL",
                "_type": "json",
                "mapX": longitude,
                "mapY": latitude,
                "radius": 12000,
                "arrange": "E",
                "numOfRows": 200,
                "pageNo": 1,
            }
        )
        url = f"https://apis.data.go.kr/B551011/KorService2/locationBasedList2?{query}"
        request = Request(url, headers={"User-Agent": "NOW-SEOUL/1.0"})
        with urlopen(request, timeout=5) as response:
            payload = json.load(response)

        items = payload["response"]["body"].get("items", {}).get("item", [])
        if isinstance(items, dict):
            items = [items]
        indexed: dict[str, dict] = {}
        for item in items:
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            indexed[title.replace(" ", "")] = item
            indexed[title.lower().replace(" ", "")] = item
        return indexed


class KakaoLocalService:
    API_URL = "https://dapi.kakao.com/v2/local/search/category.json"
    QUICK_KEYWORDS = {
        "간식",
        "국수",
        "김밥",
        "도넛",
        "떡볶이",
        "만두",
        "베이커리",
        "분식",
        "샌드위치",
        "제과",
        "패스트푸드",
    }
    MEAL_EXCLUDE_KEYWORDS = {
        "간식",
        "도넛",
        "디저트",
        "베이커리",
        "빙수",
        "아이스크림",
        "제과",
        "젤라또",
        "카페",
    }

    def __init__(self) -> None:
        self.api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
        self.cache = TTLCache(ttl_seconds=900)
        self.last_error: str | None = None

    @property
    def is_live(self) -> bool:
        return bool(self.api_key)

    @property
    def status(self) -> str:
        if not self.is_live:
            return "off"
        return "error" if self.last_error else "live"

    @property
    def status_detail(self) -> str:
        if not self.is_live:
            return "not-configured"
        return self.last_error or "ready"

    def search_nearby(
        self,
        latitude: float,
        longitude: float,
        food_preference: FoodPreference,
        reference_places: list[Place],
        radius_meters: int = 1500,
    ) -> list[Place]:
        if not self.is_live:
            return []

        radius_meters = max(300, min(radius_meters, 5000))
        cache_key = f"{latitude:.3f}:{longitude:.3f}:{food_preference}:{radius_meters // 250}"
        cached = self.cache.get(cache_key)
        if isinstance(cached, list):
            return cached

        categories = ["CE7"] if food_preference == "cafe" else ["FD6"]
        if food_preference == "any":
            categories = ["FD6", "CE7"]

        documents_by_category: dict[str, list[dict]] = {}
        successful_requests = 0
        request_errors: list[str] = []
        for category in categories:
            try:
                documents_by_category[category] = self._fetch_category(
                    category,
                    latitude,
                    longitude,
                    radius_meters,
                )
                successful_requests += 1
            except HTTPError as error:
                request_errors.append(self._http_error_reason(error))
                documents_by_category[category] = []
            except (URLError, OSError, TimeoutError):
                request_errors.append("connection-error")
                documents_by_category[category] = []
            except (ValueError, KeyError, json.JSONDecodeError):
                request_errors.append("invalid-response")
                documents_by_category[category] = []

        self.last_error = None if successful_requests else (request_errors[0] if request_errors else "upstream-error")

        places_by_category = {
            category: self._parse_documents(
                documents,
                category,
                food_preference,
                reference_places,
            )
            for category, documents in documents_by_category.items()
        }
        if food_preference == "any":
            places = places_by_category.get("FD6", [])[:5] + places_by_category.get("CE7", [])[:4]
            places.sort(key=lambda place: place.distance_meters or 999999)
        else:
            places = places_by_category.get(categories[0], [])[:9]

        self.cache.set(cache_key, places)
        return places

    @classmethod
    def _http_error_reason(cls, error: HTTPError) -> str:
        kakao_code = None
        try:
            payload = json.loads(error.read().decode("utf-8", errors="replace"))
            kakao_code = payload.get("code") if isinstance(payload, dict) else None
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        return cls._kakao_error_reason(error.code, kakao_code)

    @staticmethod
    def _kakao_error_reason(status_code: int, kakao_code: int | None) -> str:
        code_reasons = {
            -3: "feature-not-enabled",
            -4: "account-restricted",
            -5: "permission-required",
            -6: "action-not-allowed",
            -10: "quota-error",
            -12: "app-suspended",
            -13: "app-inactive",
            -401: "invalid-key-or-ip",
            -903: "unregistered-key",
        }
        if kakao_code in code_reasons:
            return code_reasons[kakao_code]
        return {
            401: "authentication-error",
            403: "permission-error",
            429: "quota-error",
        }.get(status_code, f"upstream-http-{status_code}")

    def _fetch_category(
        self,
        category: str,
        latitude: float,
        longitude: float,
        radius_meters: int,
    ) -> list[dict]:
        query = urlencode(
            {
                "category_group_code": category,
                "x": longitude,
                "y": latitude,
                "radius": radius_meters,
                "sort": "distance",
                "size": 15,
                "page": 1,
            }
        )
        request = Request(
            f"{self.API_URL}?{query}",
            headers={
                "Authorization": f"KakaoAK {self.api_key}",
                "User-Agent": "NOW-SEOUL/1.0",
            },
        )
        with urlopen(request, timeout=5) as response:
            payload = json.load(response)
        documents = payload.get("documents", [])
        if not isinstance(documents, list):
            raise ValueError("Kakao Local response did not contain a document list")
        return documents

    def _parse_documents(
        self,
        documents: list[dict],
        category_code: str,
        food_preference: FoodPreference,
        reference_places: list[Place],
    ) -> list[Place]:
        parsed: list[Place] = []
        seen_ids: set[str] = set()

        for document in documents:
            kakao_id = str(document.get("id") or "").strip()
            name = str(document.get("place_name") or "").strip()
            if not kakao_id or not name or kakao_id in seen_ids:
                continue
            try:
                latitude = float(document["y"])
                longitude = float(document["x"])
            except (KeyError, TypeError, ValueError):
                continue

            seen_ids.add(kakao_id)
            category_name = str(document.get("category_name") or "").strip()
            is_cafe = category_code == "CE7"
            is_quick = any(keyword in category_name for keyword in self.QUICK_KEYWORDS)
            if is_cafe:
                duration, minimum_duration = 40, 30
            elif food_preference == "quick":
                duration, minimum_duration = 35, 25
            elif food_preference == "meal":
                duration, minimum_duration = 55, 45
            elif is_quick:
                duration, minimum_duration = 35, 25
            else:
                duration, minimum_duration = 55, 45

            address = str(
                document.get("road_address_name") or document.get("address_name") or ""
            ).strip()
            distance_text = str(document.get("distance") or "").strip()
            distance_meters = int(distance_text) if distance_text.isdigit() else None
            hotspot = self._nearest_hotspot(latitude, longitude, reference_places)
            place_type = "cafe" if is_cafe else "restaurant"
            label_en = "Café" if is_cafe else "Restaurant"
            label_ko = "카페" if is_cafe else "음식점"

            parsed.append(
                Place(
                    id=f"kakao-{kakao_id}",
                    name_en=name,
                    name_ko=name,
                    description_en=f"Nearby {label_en.lower()} from Kakao Local",
                    description_ko=f"카카오 로컬에서 찾은 주변 {label_ko}",
                    latitude=latitude,
                    longitude=longitude,
                    duration_minutes=duration,
                    minimum_duration_minutes=minimum_duration,
                    tags=["food"],
                    hotspot=hotspot,
                    indoor=True,
                    opening_note_en="Check live hours on Kakao Map",
                    opening_note_ko="카카오맵에서 영업 여부 확인",
                    place_type=place_type,
                    data_source="kakao-local",
                    category_name=category_name or label_ko,
                    address=address or None,
                    distance_meters=distance_meters,
                    external_url=str(document.get("place_url") or "").strip() or None,
                )
            )

        if food_preference == "meal":
            meal_places = [
                place
                for place in parsed
                if not any(
                    keyword in (place.category_name or "")
                    for keyword in self.MEAL_EXCLUDE_KEYWORDS | self.QUICK_KEYWORDS
                )
            ]
            if meal_places:
                parsed = meal_places
            parsed.sort(key=lambda place: place.distance_meters or 999999)
        elif food_preference == "quick":
            parsed.sort(
                key=lambda place: (
                    not any(keyword in (place.category_name or "") for keyword in self.QUICK_KEYWORDS),
                    place.distance_meters or 999999,
                )
            )
        else:
            parsed.sort(key=lambda place: place.distance_meters or 999999)
        return parsed

    @staticmethod
    def _nearest_hotspot(latitude: float, longitude: float, reference_places: list[Place]) -> str:
        if not reference_places:
            return "명동 관광특구"

        def distance(place: Place) -> float:
            phi1, phi2 = math.radians(latitude), math.radians(place.latitude)
            delta_phi = math.radians(place.latitude - latitude)
            delta_lambda = math.radians(place.longitude - longitude)
            value = (
                math.sin(delta_phi / 2) ** 2
                + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
            )
            return 6371.0 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))

        return min(reference_places, key=distance).hotspot

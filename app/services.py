import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from app.models import CrowdSnapshot, Place


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

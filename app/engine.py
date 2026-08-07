import math
from collections import Counter
from datetime import datetime
from itertools import permutations

from app.models import (
    Course,
    CourseStop,
    CrowdSnapshot,
    Place,
    RecommendationRequest,
    TimeBudget,
)


CROWD_VALUE = {"relaxed": 0, "normal": 1, "busy": 2, "crowded": 3}
TAG_LABELS = {
    "photo": ("Photogenic Seoul", "사진으로 남기는 서울"),
    "food": ("Seoul Bites", "서울 한입 코스"),
    "culture": ("Culture Walk", "서울 문화 산책"),
    "shopping": ("Local Finds", "서울 발견 쇼핑"),
    "nature": ("Green Pause", "도심 속 초록 쉼표"),
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def walking_minutes(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    distance = haversine_km(lat1, lon1, lat2, lon2)
    adjusted_distance = distance * 1.22
    return max(2, math.ceil(adjusted_distance / 4.5 * 60))


def is_open(place: Place, now: datetime) -> bool:
    if place.open_24h:
        return True
    if now.weekday() in place.closed_weekdays:
        return False
    if place.opening_hour is None or place.closing_hour is None:
        return True
    return place.opening_hour <= now.hour < place.closing_hour


def candidate_places(request: RecommendationRequest, places: list[Place], now: datetime) -> list[Place]:
    radius = 0.4 + request.available_minutes / 30
    open_places = [place for place in places if is_open(place, now)]

    ranked = sorted(
        open_places,
        key=lambda place: (
            -len(set(place.tags) & set(request.preferences)),
            haversine_km(request.latitude, request.longitude, place.latitude, place.longitude),
        ),
    )
    nearby = [
        place
        for place in ranked
        if haversine_km(request.latitude, request.longitude, place.latitude, place.longitude) <= radius
    ]
    return (nearby if len(nearby) >= 4 else ranked[:10])[:14]


def _crowd_score(level: str, tolerance: str) -> float:
    value = CROWD_VALUE[level]
    penalties = {
        "low": [1.0, 0.78, 0.35, 0.05],
        "medium": [1.0, 0.88, 0.62, 0.28],
        "high": [1.0, 0.94, 0.82, 0.62],
    }
    return penalties[tolerance][value]


def _sequence_metrics(
    sequence: tuple[Place, ...],
    request: RecommendationRequest,
    crowds: dict[str, CrowdSnapshot],
) -> dict | None:
    travel_minutes = 0
    current_lat, current_lon = request.latitude, request.longitude
    leg_minutes: list[int] = []

    for place in sequence:
        leg = walking_minutes(current_lat, current_lon, place.latitude, place.longitude)
        if leg > 38:
            return None
        leg_minutes.append(leg)
        travel_minutes += leg
        current_lat, current_lon = place.latitude, place.longitude

    buffer_minutes = max(10, round(request.available_minutes * 0.08 / 5) * 5)
    available_for_visits = request.available_minutes - travel_minutes - buffer_minutes
    minimum_visit = 20 if request.available_minutes <= 90 else 30
    minimum_durations = [
        min(
            place.duration_minutes,
            place.minimum_duration_minutes
            if place.minimum_duration_minutes is not None
            else minimum_visit,
        )
        for place in sequence
    ]
    if sum(minimum_durations) > available_for_visits:
        return None

    visit_durations = minimum_durations[:]
    remaining = available_for_visits - sum(visit_durations)
    while remaining >= 5:
        expanded = False
        for index, place in enumerate(sequence):
            if visit_durations[index] + 5 <= place.duration_minutes and remaining >= 5:
                visit_durations[index] += 5
                remaining -= 5
                expanded = True
        if not expanded:
            break

    visit_minutes = sum(visit_durations)
    total_minutes = travel_minutes + visit_minutes + buffer_minutes
    if total_minutes > request.available_minutes:
        return None

    preference_scores = [
        1.0
        if place.place_type in {"restaurant", "cafe"} and request.food_stop != "none"
        else len(set(place.tags) & set(request.preferences)) / max(1, len(set(request.preferences)))
        for place in sequence
    ]
    preference_score = sum(preference_scores) / len(preference_scores)
    crowd_score = sum(
        _crowd_score(crowds[place.hotspot].level, request.crowd_tolerance) for place in sequence
    ) / len(sequence)
    time_fit = total_minutes / request.available_minutes
    distance_score = max(0.0, 1 - travel_minutes / max(35, request.available_minutes * 0.45))
    matched_tags = set().union(*(set(place.tags) & set(request.preferences) for place in sequence))
    variety_score = len(matched_tags) / len(set(request.preferences))
    score = round(
        100
        * (
            preference_score * 0.38
            + crowd_score * 0.25
            + time_fit * 0.20
            + distance_score * 0.12
            + variety_score * 0.05
        )
    )
    return {
        "score": score,
        "travel_minutes": travel_minutes,
        "visit_minutes": visit_minutes,
        "buffer_minutes": buffer_minutes,
        "total_minutes": total_minutes,
        "leg_minutes": leg_minutes,
        "visit_durations": visit_durations,
        "food_minutes": sum(
            duration
            for place, duration in zip(sequence, visit_durations)
            if place.place_type in {"restaurant", "cafe"}
        ),
        "crowd_value": max(CROWD_VALUE[crowds[place.hotspot].level] for place in sequence),
        "preference_score": preference_score,
    }


def _overlap(left: tuple[Place, ...], right: tuple[Place, ...]) -> float:
    left_ids = {place.id for place in left}
    right_ids = {place.id for place in right}
    return len(left_ids & right_ids) / len(left_ids | right_ids)


def _select_diverse(options: list[tuple[tuple[Place, ...], dict]]) -> list[tuple[tuple[Place, ...], dict]]:
    if not options:
        return []
    selected = [options[0]]

    quiet_options = sorted(options[1:80], key=lambda item: (item[1]["crowd_value"], -item[1]["score"]))
    quiet = next((item for item in quiet_options if _overlap(selected[0][0], item[0]) <= 0.6), None)
    if quiet is not None:
        selected.append(quiet)

    for option in options[1:]:
        if option in selected:
            continue
        if all(_overlap(existing[0], option[0]) <= 0.65 for existing in selected):
            selected.append(option)
        if len(selected) == 3:
            break

    for option in options:
        if len(selected) == 3:
            break
        if option not in selected:
            selected.append(option)
    return selected


def _contains_food(sequence: tuple[Place, ...]) -> bool:
    return any(place.place_type in {"restaurant", "cafe"} for place in sequence)


def _select_for_food_mode(
    options: list[tuple[tuple[Place, ...], dict]],
    mode: str,
) -> list[tuple[tuple[Place, ...], dict]]:
    food_options = [option for option in options if _contains_food(option[0])]
    attraction_options = [option for option in options if not _contains_food(option[0])]

    if mode == "required":
        return _select_diverse(food_options)
    if mode == "none" or not food_options:
        return _select_diverse(attraction_options)

    plain_selected = _select_diverse(attraction_options)
    selected: list[tuple[tuple[Place, ...], dict]] = []
    if plain_selected:
        selected.append(plain_selected[0])

    food_choice = next(
        (
            option
            for option in food_options
            if all(_overlap(existing[0], option[0]) <= 0.75 for existing in selected)
        ),
        food_options[0],
    )
    selected.append(food_choice)

    for option in plain_selected[1:]:
        if all(_overlap(existing[0], option[0]) <= 0.65 for existing in selected):
            selected.append(option)
        if len(selected) == 3:
            break
    for option in attraction_options:
        if len(selected) == 3:
            break
        if option not in selected:
            selected.append(option)
    return selected


def recommend_courses(
    request: RecommendationRequest,
    places: list[Place],
    crowds: dict[str, CrowdSnapshot],
) -> list[Course]:
    options: list[tuple[tuple[Place, ...], dict]] = []
    max_stops = 3 if request.available_minutes >= 150 else 2
    for length in range(1, max_stops + 1):
        for sequence in permutations(places, length):
            food_stop_count = sum(
                place.place_type in {"restaurant", "cafe"} for place in sequence
            )
            if food_stop_count > 1:
                continue
            if request.food_stop == "none" and food_stop_count:
                continue
            metrics = _sequence_metrics(sequence, request, crowds)
            if metrics is not None:
                options.append((sequence, metrics))

    options.sort(key=lambda item: item[1]["score"], reverse=True)
    selected = _select_for_food_mode(options, request.food_stop)
    badges = (
        ["BEST FIT", "FOOD OPTION", "ALTERNATIVE"]
        if request.language == "en" and request.food_stop == "optional"
        else ["가장 잘 맞아요", "식사·카페 선택", "다른 선택지"]
        if request.language == "ko" and request.food_stop == "optional"
        else ["BEST FIT", "LOW CROWDS", "ALTERNATIVE"]
        if request.language == "en"
        else ["가장 잘 맞아요", "한적한 코스", "다른 선택지"]
    )
    courses: list[Course] = []

    for index, (sequence, metrics) in enumerate(selected):
        food_places = [
            place for place in sequence if place.place_type in {"restaurant", "cafe"}
        ]
        if food_places:
            if food_places[0].place_type == "cafe":
                title_en, title_ko = "Seoul Café Pause", "서울 카페 쉼표"
            else:
                title_en, title_ko = "Seoul & Local Bite", "서울 로컬 한 끼"
        else:
            tag_counts = Counter(
                tag for place in sequence for tag in place.tags if tag in request.preferences
            )
            dominant_tag = tag_counts.most_common(1)[0][0] if tag_counts else request.preferences[0]
            title_en, title_ko = TAG_LABELS[dominant_tag]
        stop_names = [place.name_en if request.language == "en" else place.name_ko for place in sequence]
        summary = " → ".join(stop_names)
        elapsed = 0
        stops = []
        route = [[request.latitude, request.longitude]]

        for stop_index, (place, leg, visit_duration) in enumerate(
            zip(sequence, metrics["leg_minutes"], metrics["visit_durations"]), start=1
        ):
            elapsed += leg
            arrival = elapsed
            elapsed += visit_duration
            stops.append(
                CourseStop(
                    order=stop_index,
                    place=place,
                    crowd=crowds[place.hotspot],
                    travel_from_previous_minutes=leg,
                    visit_minutes=visit_duration,
                    arrival_minute=arrival,
                    leave_minute=elapsed,
                )
            )
            route.append([place.latitude, place.longitude])

        worst_level = max((crowds[place.hotspot].level for place in sequence), key=CROWD_VALUE.get)
        courses.append(
            Course(
                id=f"course-{index + 1}",
                badge=badges[index],
                title=title_en if request.language == "en" else title_ko,
                summary=summary,
                score=metrics["score"],
                crowd_level=worst_level,
                time_budget=TimeBudget(
                    travel_minutes=metrics["travel_minutes"],
                    visit_minutes=metrics["visit_minutes"],
                    activity_minutes=metrics["visit_minutes"] - metrics["food_minutes"],
                    food_minutes=metrics["food_minutes"],
                    buffer_minutes=metrics["buffer_minutes"],
                    unused_minutes=request.available_minutes - metrics["total_minutes"],
                    total_minutes=metrics["total_minutes"],
                ),
                stops=stops,
                route=route,
            )
        )
    return courses

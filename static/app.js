const translations = {
  en: {
    eyebrow: "YOUR NEXT SEOUL MOMENT",
    heroTitle: "One free hour?<br /><em>Make it feel like Seoul.</em>",
    heroDescription: "Tell us where you are, how much time you have, and what feels like you. We’ll make three Seoul routes that fit before your next plan.",
    startPlanning: "Plan a route",
    proofTime: "FREE TIME", proofRoutes: "ROUTES", proofCrowds: "CROWD SIGNAL",
    plannerTitle: "What does your free time look like?", plannerDescription: "Four quick choices. No account, no over-planning.",
    locationTitle: "Where are you now?", locationHint: "Use GPS or pick a nearby hub", useLocation: "Use my current location",
    timeTitle: "How much time is yours?", timeHint: "We always keep a safety buffer", hours: "HOURS",
    tasteTitle: "What are you in the mood for?", tasteHint: "Choose as many as you like",
    photo: "Photo", food: "Food", culture: "Culture", shopping: "Shopping", nature: "Nature",
    crowdTitle: "How do you feel about crowds?", crowdHint: "We’ll tune the route around you",
    avoidCrowds: "Avoid them", avoidCrowdsHint: "Quiet route first", someCrowds: "Some are fine", someCrowdsHint: "Balanced route", anyCrowds: "I don’t mind", anyCrowdsHint: "Best-known spots",
    findRoutes: "Find my Seoul", routesReady: "YOUR ROUTES ARE READY", resultsTitle: "Three ways to spend the moment.",
    routeView: "ROUTE VIEW", mapFallback: "Map tiles are unavailable. Your stop order is still shown in the route cards.",
    youAreHere: "You are here", recommendedStop: "Recommended stop", routeEstimate: "Route line and walking time are estimates",
    methodTitle: "Not another full itinerary.<br /><em>Just the right next move.</em>",
    methodDescription: "NOW SEOUL filters what is open, scores what matches your mood, checks nearby crowd signals, and only keeps routes that fit your real time budget.",
    methodOne: "Find nearby places", methodTwo: "Respect the clock", methodThree: "Tune for the moment",
    loadingTitle: "Making time fit...", loadingHint: "Checking distance, stays and crowd signals",
    selected: "selected", locating: "Finding your location...", gpsReady: "Current location ready", gpsDenied: "Location unavailable — choose a hub below",
    travel: "TRAVEL", visit: "VISIT", buffer: "BUFFER", min: "MIN", score: "FIT", crowd: "CROWD", stayTime: "Suggested stay",
    sourceLive: "LIVE SEOUL DATA", sourceEstimated: "ESTIMATED DATA", requestError: "We couldn’t build the routes. Check the API server and try again.",
    preferenceError: "Choose at least one activity.", yourRoute: "Your Seoul route",
  },
  ko: {
    eyebrow: "지금, 다음 서울의 순간",
    heroTitle: "남는 한 시간,<br /><em>서울의 한 장면으로.</em>",
    heroDescription: "현재 위치와 남은 시간, 취향을 알려주세요. 다음 일정 전에 딱 맞는 서울 코스 세 가지를 만들어 드립니다.",
    startPlanning: "지금 코스 만들기",
    proofTime: "남는 시간", proofRoutes: "추천 코스", proofCrowds: "혼잡 신호",
    plannerTitle: "지금 남은 시간은 어떤 모습인가요?", plannerDescription: "네 가지만 고르면 됩니다. 가입도, 복잡한 계획도 필요 없어요.",
    locationTitle: "지금 어디에 있나요?", locationHint: "GPS를 사용하거나 가까운 지역 선택", useLocation: "현재 위치 사용하기",
    timeTitle: "얼마나 시간이 남았나요?", timeHint: "항상 안전 여유시간을 남겨요", hours: "시간",
    tasteTitle: "지금 무엇을 하고 싶나요?", tasteHint: "여러 개 선택할 수 있어요",
    photo: "사진", food: "음식", culture: "문화", shopping: "쇼핑", nature: "자연",
    crowdTitle: "혼잡한 장소는 어떤가요?", crowdHint: "선호에 맞춰 코스를 조정해요",
    avoidCrowds: "피하고 싶어요", avoidCrowdsHint: "한적한 코스 우선", someCrowds: "조금은 괜찮아요", someCrowdsHint: "균형 잡힌 코스", anyCrowds: "상관없어요", anyCrowdsHint: "대표 명소 우선",
    findRoutes: "내 서울 코스 찾기", routesReady: "코스가 준비됐어요", resultsTitle: "지금 시간을 보내는 세 가지 방법.",
    routeView: "경로 보기", mapFallback: "지도 타일을 불러오지 못했습니다. 추천 순서는 코스 카드에서 확인할 수 있어요.",
    youAreHere: "현재 위치", recommendedStop: "추천 장소", routeEstimate: "경로선과 도보시간은 추정치입니다",
    methodTitle: "거창한 여행 계획이 아니라,<br /><em>지금 딱 좋은 다음 장소.</em>",
    methodDescription: "NOW SEOUL은 현재 운영 중인 장소를 찾고, 취향과 혼잡도를 평가한 뒤 실제 시간 예산에 들어오는 코스만 남깁니다.",
    methodOne: "가까운 장소 찾기", methodTwo: "남은 시간 지키기", methodThree: "지금의 취향 반영하기",
    loadingTitle: "시간을 맞추는 중...", loadingHint: "거리와 체류시간, 혼잡 신호를 확인하고 있어요",
    selected: "선택됨", locating: "현재 위치를 찾는 중...", gpsReady: "현재 위치 확인 완료", gpsDenied: "위치를 확인할 수 없어요 — 아래 지역을 선택해 주세요",
    travel: "이동", visit: "관광", buffer: "여유", min: "분", score: "적합", crowd: "혼잡", stayTime: "추천 체류시간",
    sourceLive: "서울 실시간 데이터", sourceEstimated: "추정 데이터", requestError: "코스를 만들지 못했습니다. API 서버를 확인하고 다시 시도해 주세요.",
    preferenceError: "활동을 한 개 이상 선택해 주세요.", yourRoute: "나의 서울 코스",
  },
};

const state = {
  language: "en",
  latitude: 37.5636,
  longitude: 126.9869,
  locationName: "Myeongdong",
  availableMinutes: 120,
  preferences: new Set(["photo", "culture"]),
  crowdTolerance: "low",
  courses: [],
  selectedCourse: 0,
  map: null,
  mapLayers: [],
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const t = (key) => translations[state.language][key] ?? key;

const escapeHTML = (value) => String(value).replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
})[character]);

const updateClock = () => {
  const time = new Intl.DateTimeFormat(state.language === "ko" ? "ko-KR" : "en-GB", {
    timeZone: "Asia/Seoul", hour: "2-digit", minute: "2-digit", hour12: false,
  }).format(new Date());
  $("#seoul-clock").textContent = `SEOUL · ${time}`;
};

const applyLanguage = () => {
  document.documentElement.lang = state.language;
  $$('[data-i18n]').forEach((element) => { element.textContent = t(element.dataset.i18n); });
  $$('[data-i18n-html]').forEach((element) => { element.innerHTML = t(element.dataset.i18nHtml); });
  $$("[data-language]").forEach((button) => button.classList.toggle("active", button.dataset.language === state.language));
  $("#location-status").textContent = `${state.locationName} · ${t("selected")}`;
  updateClock();
  if (state.courses.length) runRecommendation(false);
};

const setExclusiveActive = (buttons, selected) => {
  buttons.forEach((button) => button.classList.toggle("active", button === selected));
};

$$("[data-language]").forEach((button) => button.addEventListener("click", () => {
  state.language = button.dataset.language;
  applyLanguage();
}));

$$(".preset").forEach((button) => button.addEventListener("click", () => {
  state.latitude = Number(button.dataset.lat);
  state.longitude = Number(button.dataset.lon);
  state.locationName = button.textContent.trim();
  setExclusiveActive($$(".preset"), button);
  $("#location-status").textContent = `${state.locationName} · ${t("selected")}`;
}));

$("#gps-button").addEventListener("click", () => {
  const status = $("#location-status");
  if (!navigator.geolocation) {
    status.textContent = t("gpsDenied");
    return;
  }
  status.textContent = t("locating");
  navigator.geolocation.getCurrentPosition(
    (position) => {
      state.latitude = position.coords.latitude;
      state.longitude = position.coords.longitude;
      state.locationName = state.language === "ko" ? "현재 위치" : "Current location";
      $$(".preset").forEach((button) => button.classList.remove("active"));
      status.textContent = `${t("gpsReady")} · ±${Math.round(position.coords.accuracy)}m`;
    },
    () => { status.textContent = t("gpsDenied"); },
    { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 },
  );
});

$$("[data-minutes]").forEach((button) => button.addEventListener("click", () => {
  state.availableMinutes = Number(button.dataset.minutes);
  $("#time-hours").textContent = String(state.availableMinutes / 60);
  setExclusiveActive($$("[data-minutes]"), button);
}));

$$("[data-preference]").forEach((button) => button.addEventListener("click", () => {
  const preference = button.dataset.preference;
  if (state.preferences.has(preference)) state.preferences.delete(preference);
  else state.preferences.add(preference);
  const active = state.preferences.has(preference);
  button.classList.toggle("active", active);
  button.setAttribute("aria-pressed", String(active));
}));

$$("[data-crowd]").forEach((button) => button.addEventListener("click", () => {
  state.crowdTolerance = button.dataset.crowd;
  setExclusiveActive($$("[data-crowd]"), button);
}));

const crowdMeta = (level) => ({
  relaxed: { color: "#4c9a73", en: "Relaxed", ko: "여유" },
  normal: { color: "#8fae71", en: "Normal", ko: "보통" },
  busy: { color: "#e1a33c", en: "Busy", ko: "약간 붐빔" },
  crowded: { color: "#d85c48", en: "Crowded", ko: "붐빔" },
})[level];

const placeName = (place) => state.language === "ko" ? place.name_ko : place.name_en;
const openingNote = (place) => state.language === "ko" ? place.opening_note_ko : place.opening_note_en;

const renderCourseCard = (course, index) => {
  const budget = course.time_budget;
  const totalAvailable = state.availableMinutes;
  const travelWidth = budget.travel_minutes / totalAvailable * 100;
  const visitWidth = budget.visit_minutes / totalAvailable * 100;
  const bufferWidth = budget.buffer_minutes / totalAvailable * 100;
  const stops = course.stops.map((stop) => {
    const crowd = crowdMeta(stop.crowd.level);
    return `
      <li data-order="${stop.order}">
        <span>
          <strong>${escapeHTML(placeName(stop.place))}</strong>
          <small>${stop.travel_from_previous_minutes} ${t("min")} ${t("travel").toLowerCase()} · ${escapeHTML(openingNote(stop.place))}</small>
          <span class="crowd-label" style="--crowd-color:${crowd.color}"><i></i>${t("crowd")} · ${crowd[state.language]}</span>
        </span>
        <time>${stop.visit_minutes} ${t("min")}</time>
      </li>`;
  }).join("");

  return `
    <button class="course-card ${index === state.selectedCourse ? "active" : ""}" type="button" data-course-index="${index}">
      <span class="course-card-main">
        <span class="course-index">0${index + 1}</span>
        <span class="course-heading">
          <small>${escapeHTML(course.badge)}</small>
          <h3>${escapeHTML(course.title)}</h3>
          <p>${escapeHTML(course.stops.map((stop) => placeName(stop.place)).join(" → "))}</p>
        </span>
        <span class="score-ring">${course.score}</span>
      </span>
      <span class="course-card-details">
        <ol class="stop-list">${stops}</ol>
        <span class="budget-label"><span>TIME BUDGET</span><span>${budget.total_minutes} / ${totalAvailable} ${t("min")}</span></span>
        <span class="time-budget">
          <i class="budget-travel" style="width:${travelWidth}%"></i>
          <i class="budget-visit" style="width:${visitWidth}%"></i>
          <i class="budget-buffer" style="width:${bufferWidth}%"></i>
        </span>
        <span class="budget-legend">
          <span><i class="budget-travel"></i>${t("travel")} ${budget.travel_minutes}</span>
          <span><i class="budget-visit"></i>${t("visit")} ${budget.visit_minutes}</span>
          <span><i class="budget-buffer"></i>${t("buffer")} ${budget.buffer_minutes}</span>
        </span>
      </span>
    </button>`;
};

const renderCourses = () => {
  $("#course-list").innerHTML = state.courses.map(renderCourseCard).join("");
  $$("[data-course-index]").forEach((button) => button.addEventListener("click", () => {
    state.selectedCourse = Number(button.dataset.courseIndex);
    renderCourses();
    renderMap(state.courses[state.selectedCourse]);
  }));
};

const clearMapLayers = () => {
  if (!state.map) return;
  state.mapLayers.forEach((layer) => layer.remove());
  state.mapLayers = [];
};

const markerIcon = (label, origin = false) => window.L.divIcon({
  className: "",
  html: `<span class="map-marker ${origin ? "origin" : ""}">${label}</span>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const initializeMap = () => {
  if (!window.L) {
    $("#route-map").hidden = true;
    $("#map-fallback").hidden = false;
    return;
  }
  state.map = window.L.map("route-map", { zoomControl: false, scrollWheelZoom: false });
  window.L.control.zoom({ position: "bottomright" }).addTo(state.map);
  window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(state.map);
  state.map.setView([state.latitude, state.longitude], 14);
};

const renderMap = (course) => {
  if (!state.map || !course) return;
  clearMapLayers();
  const route = course.route.map(([lat, lon]) => [lat, lon]);
  const line = window.L.polyline(route, { color: "#e76545", weight: 4, opacity: .9, dashArray: "8 8" }).addTo(state.map);
  state.mapLayers.push(line);

  const origin = window.L.marker(route[0], { icon: markerIcon("YOU", true) }).addTo(state.map).bindPopup(t("youAreHere"));
  state.mapLayers.push(origin);
  course.stops.forEach((stop, index) => {
    const marker = window.L.marker([stop.place.latitude, stop.place.longitude], { icon: markerIcon(String(index + 1)) })
      .addTo(state.map)
      .bindPopup(`<b>${escapeHTML(placeName(stop.place))}</b><br>${t("stayTime")} · ${stop.visit_minutes}${state.language === "ko" ? "" : " "}${t("min")}`);
    state.mapLayers.push(marker);
  });
  state.map.fitBounds(line.getBounds(), { padding: [45, 45], maxZoom: 15 });
  $("#map-title").textContent = course.title || t("yourRoute");
  setTimeout(() => state.map.invalidateSize(), 50);
};

const runRecommendation = async (scrollToResults = true) => {
  const error = $("#form-error");
  error.hidden = true;
  if (!state.preferences.size) {
    error.textContent = t("preferenceError");
    error.hidden = false;
    return;
  }

  $("#loading-overlay").hidden = false;
  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        latitude: state.latitude,
        longitude: state.longitude,
        available_minutes: state.availableMinutes,
        preferences: [...state.preferences],
        crowd_tolerance: state.crowdTolerance,
        language: state.language,
      }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed: ${response.status}`);
    }
    const data = await response.json();
    state.courses = data.courses;
    state.selectedCourse = 0;
    $("#results-notice").textContent = data.notice;
    $("#source-pill").textContent = data.data_sources.seoul_city_data === "live" ? t("sourceLive") : t("sourceEstimated");
    renderCourses();
    renderMap(state.courses[0]);
    $("#results").hidden = false;
    if (scrollToResults) $("#results").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (requestError) {
    console.error(requestError);
    error.textContent = `${t("requestError")} ${requestError.message}`;
    error.hidden = false;
  } finally {
    $("#loading-overlay").hidden = true;
  }
};

$("#planner-form").addEventListener("submit", (event) => {
  event.preventDefault();
  runRecommendation();
});

initializeMap();
applyLanguage();
updateClock();
setInterval(updateClock, 30000);

fetch("/api/config")
  .then((response) => response.ok ? response.json() : Promise.reject(new Error("Config unavailable")))
  .then((config) => {
    $("#source-pill").textContent = config.data_sources.seoul_city_data === "live" ? t("sourceLive") : t("sourceEstimated");
  })
  .catch((error) => console.warn(error))
  .finally(() => {
    if (new URLSearchParams(window.location.search).get("demo") === "1") {
      runRecommendation(false);
    }
  });

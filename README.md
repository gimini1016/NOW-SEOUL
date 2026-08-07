# NOW SEOUL

**Turn your free time into Seoul time.**

NOW SEOUL은 외국인 관광객이 서울에서 1~4시간의 애매한 여유시간을 활용할 수 있도록
현재 위치, 남은 시간, 취향, 혼잡도 선호를 바탕으로 즉석 코스 TOP 3를 추천하는 MVP입니다.

## 현재 구현 범위

- 브라우저 GPS 또는 명동·서울역·광화문·홍대·강남 출발지 선택
- 1~4시간 Time Budget
- Photo·Food·Culture·Shopping·Nature 다중 취향 선택
- 혼잡 회피 수준 반영
- 영업시간과 휴무일을 고려한 후보 필터
- `이동 + 체류 + 안전 여유시간 ≤ 남은 시간` 제약을 만족하는 코스 TOP 3
- 영어·한국어 전환
- 지도 경로, 장소별 도보시간, 체류시간, 혼잡도
- 이동·관광·여유시간을 나눈 Time Budget 시각화
- TourAPI 이미지 및 서울 실시간 인구 혼잡도 선택적 연동
- 외부 API 키나 네트워크 장애 시 데모 데이터로 자동 폴백

## 빠른 실행

```bash
cd NOW-SEOUL
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload
```

브라우저에서 아래 주소를 엽니다.

- 서비스: <http://localhost:8000>
- API 문서: <http://localhost:8000/docs>
- 상태 확인: <http://localhost:8000/api/health>

별도 프런트엔드 서버가 필요하지 않습니다. FastAPI가 홈페이지와 API를 같은 주소에서
제공하므로 로컬 개발 중 CORS와 HTTPS/localhost 혼합 문제를 피할 수 있습니다.

## 실제 공공데이터 연결

키가 없어도 앱은 동작합니다. 실제 데이터를 사용하려면 `.env.example`을 복사해 `.env`를
만들고 아래 값을 입력합니다.

```dotenv
TOUR_API_KEY=공공데이터포털에서_발급한_키
SEOUL_OPEN_DATA_KEY=서울열린데이터광장에서_발급한_키
ALLOWED_ORIGINS=*
```

그다음 환경파일을 지정해 실행합니다.

```bash
uvicorn app.main:app --reload --env-file .env
```

API 키는 절대 `static/app.js`나 GitHub 저장소에 넣지 마세요. `.env`는 `.gitignore`에
포함되어 있습니다.

## API

| Method | Endpoint | 설명 |
|---|---|---|
| `GET` | `/api/health` | 서버 상태 |
| `GET` | `/api/config` | 프리셋과 데이터 소스 상태 |
| `GET` | `/api/places` | 기본 관광지 목록 |
| `POST` | `/api/recommend` | 조건 기반 코스 TOP 3 |

추천 요청 예시:

```json
{
  "latitude": 37.5636,
  "longitude": 126.9869,
  "available_minutes": 120,
  "preferences": ["photo", "culture"],
  "crowd_tolerance": "low",
  "language": "en"
}
```

## 추천 방식

1. 현재 운영 중인 장소를 필터링합니다.
2. 남은 시간에 따라 검색 반경을 정하고 가까운 후보를 선택합니다.
3. 최대 3개 장소의 순서를 조합합니다.
4. 각 조합에 대해 도보 이동시간, 체류시간, 안전 여유시간을 계산합니다.
5. 제한시간을 넘는 조합은 제거합니다.
6. 취향 38%, 혼잡도 25%, 시간 활용도 20%, 이동 효율 12%, 다양성 5%로 평가합니다.
7. 장소가 과도하게 겹치지 않는 세 코스를 반환합니다.

## 테스트

```bash
pytest -q
```

테스트는 거리·도보시간, 90분 및 120분 시간 제약, API 입력 검증, 홈페이지 제공을 확인합니다.

## 데이터 한계

- 기본 관광지 27곳의 체류시간과 취향 태그는 MVP용 큐레이션 데이터입니다.
- 서울 실시간 혼잡도는 개별 관광지가 아니라 서울시 핫스팟 권역 단위입니다.
- 현재 지도 경로는 실제 보행 도로망이 아닌 좌표 기반 직선 경로이며, 도보시간에는 우회계수
  1.22를 적용합니다. 다음 단계에서 카카오맵 경로 API로 교체할 수 있습니다.
- 운영시간은 계절·행사에 따라 달라질 수 있어 결과 화면에 확인 안내를 표시합니다.
- 다음 일정의 위치는 아직 입력받지 않으며, 현재는 안전 여유시간으로 지각 위험을 줄입니다.

## Render 배포

`render.yaml`이 포함되어 있습니다. Render에서 이 저장소를 Web Service로 연결하면 다음
명령으로 실행됩니다.

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

배포 환경변수에 `TOUR_API_KEY`, `SEOUL_OPEN_DATA_KEY`를 추가하면 실시간 모드로 전환됩니다.

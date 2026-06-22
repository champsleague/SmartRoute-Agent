# SmartRoute 🚗 서울 실시간 "주차 우선" 길 안내 AI 에이전트

> 목적지를 말하면 **주차 자리를 먼저 확보하고, 그 주차장까지 가는 접근 경로**를 한 번에 안내하는 멀티에이전트 서비스.
> Microsoft Agent Framework(Python) + Azure OpenAI + 서울 실시간 도시데이터로 구현.

---

## 💡 컨셉

운전자는 보통 길찾기 앱과 주차 앱을 따로 봅니다. 하지만 **빠르게 도착해도 댈 곳이 없으면 의미가 없습니다.**
그래서 SmartRoute는 순서를 뒤집습니다:

> **① 목적지 주변의 실시간 여유 주차장을 먼저 찾고 → ② 그 주차장까지의 접근 소통(경로)을 안내**

흩어진 실시간 공공데이터를 여러 전문 AI 에이전트가 협업해 하나의 추천으로 종합합니다.

---

## 🤖 에이전트 구성 (멀티에이전트 오케스트레이션)

| 에이전트 | 페르소나 | 역할 | 도구 |
|----------|----------|------|------|
| **Coordinator** | 길안내 컨시어지 | 사용자와 대화, 목적지→핫스팟 매핑, 두 전문가 호출·**종합** | (전문가를 도구로 사용) |
| **ParkingAgent** | 주차 도우미 | 지역 실시간 주차 현황 분석, 여유 많은 주차장 추천 | `get_parking_status(지역)` |
| **RouteAgent** | 교통 분석가 | 그 지역까지의 실시간 도로소통(접근) 분석 | `get_road_traffic(지역)` |

**오케스트레이션 방식 — agent-as-tool:** Coordinator가 ParkingAgent·RouteAgent를 *도구처럼* 호출합니다.
실제 흐름은 **주차 우선 → 접근 경로** 순서로 동작합니다.

```
사용자 (Chainlit 웹 챗)
        │  "여의도 IFC몰 가는데 주차하고 길 알려줘"
   ┌────▼─────────┐
   │ Coordinator  │  ← 목적지 파악·종합 (Azure OpenAI)
   └──┬───────┬───┘
      │ ①주차  │ ②접근경로   (agent-as-tool)
 ┌────▼──┐ ┌──▼─────┐
 │Parking│ │ Route  │
 │ Agent │ │ Agent  │
 └───┬───┘ └───┬────┘
   @tool      @tool
     └────┬─────┘
   서울 실시간 도시데이터(citydata) API
```

### 가드레일 (행동 규칙)
- **수치는 실제 도구 데이터에서만 인용** — 추측/창작 금지(환각 0), 갱신시각 표기
- **한국어로만** 답변, 같은 목적지 반복 재질문 금지(세션 메모리로 맥락 유지)
- 서울 핫스팟 단위 안내(정밀 turn-by-turn 내비게이션은 비목표)

---

## 🛠 기술 스택

- **에이전트 SDK**: Microsoft Agent Framework (Python, `agent-framework`)
- **LLM(두뇌)**: Azure OpenAI (`gpt-4o-mini`) — `OpenAIChatCompletionClient(azure_endpoint=...)`
- **데이터**: 서울 실시간 도시데이터(citydata, OA-21285) — 주차(`PRK_STTS`) + 도로소통(`ROAD_TRAFFIC_STTS`)
- **UI**: Chainlit 웹 챗
- **부가**: 주차장별 **네이버 지도 링크** 자동 첨부 (전화 `tel:` 링크는 데이터 확보 시 자동 표시)

---

## 📁 폴더 구조

```
HDK_MS/
├── app.py                       # Chainlit 웹 챗 진입점
├── src/
│   ├── config.py                # .env 로드 (Azure / Seoul 키)
│   ├── llm.py                   # Azure OpenAI 클라이언트 팩토리
│   ├── clients/seoul_citydata.py# citydata 호출 + 주차/도로 추출
│   ├── tools/                   # @tool: get_parking_status / get_road_traffic
│   ├── agents/                  # parking_agent · route_agent · coordinator
│   ├── hotspots.py              # 목적지 → 핫스팟 매핑
│   └── main.py                  # 콘솔 챗(대안 실행)
├── scripts/smoke_citydata.py    # LLM 없이 데이터 계층 점검
├── agent.md / prd.md / trd.md   # 컨셉·요구사항·기술 문서
└── presentation_script.md       # 발표 스크립트
```

---

## 🚀 실행 방법

### 1) 설치 (Python 3.13 권장)
```bash
python -m venv .venv
.venv\Scripts\python -m pip install --pre -r requirements.txt
```

### 2) 환경변수 — `.env.sample` 을 복사해 `.env` 작성 (커밋 금지)
```
SEOUL_API_KEY=<서울 열린데이터 인증키>
AZURE_OPENAI_ENDPOINT=<...>.openai.azure.com/
AZURE_OPENAI_API_KEY=<...>
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini     # Azure OpenAI 배포 이름
```

### 3) 실행
```bash
# 웹 UI
.venv\Scripts\chainlit run app.py -w        # http://localhost:8000

# 콘솔
.venv\Scripts\python -m src.main

# 데이터만 점검(LLM 불필요)
.venv\Scripts\python -m scripts.smoke_citydata 여의도
```

---

## 🔭 확장 계획
- **실제 경로 API**(Tmap/Kakao)로 ETA·턴바이턴 경로 (citydata는 현재 지역 접근 소통으로 근사)
- **서울 공영주차장 API**로 실시간 주차 커버리지 확대 + 전화번호(`tel:`) 연결
- Azure Container Apps 배포(`azd`)

---

*Microsoft Agent Framework 해커톤 (GitHub Copilot & MAF) 출품작  (1위)*

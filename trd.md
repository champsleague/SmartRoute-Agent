# SmartRoute — Technical Requirements Document (TRD)

> 구현 기준 기술 문서. PRD/AGENT.md의 컨셉·가드레일을 코드로 옮기기 위한 스택·구조·인터페이스를 정의한다.
> 런타임: **Python + Microsoft Agent Framework (`agent-framework`)**.

---

## 1. 기술 스택
| 영역 | 선택 | 비고 |
|------|------|------|
| 에이전트 SDK | **Microsoft Agent Framework (Python)** `agent-framework` (preview, `--pre`) | ChatAgent, 도구, 오케스트레이션 |
| LLM 통합 | `agent-framework-azure-ai` (Azure OpenAI / Microsoft Foundry) | 대안: GitHub Models / OpenAI |
| HTTP 클라이언트 | `httpx` (async) | 서울 citydata 호출 |
| 데이터 검증 | `pydantic` (MAF 의존성으로 포함) | 응답 모델/구조화 출력 |
| 설정 | `python-dotenv` (.env) | 키/엔드포인트 주입 |
| UI(옵션) | 콘솔 챗(MVP) → 필요 시 `chainlit` 또는 `FastAPI`+간단 프론트 | 데모 |
| 런타임 | Python 3.11~3.13 권장 | ⚠️ 3.14는 최신 — 일부 preview 휠 미호환 가능, §9 참고 |
| 데이터 | 서울 실시간 도시데이터(citydata, OA-21285) | 핫스팟 단위 주차+도로 |

설치:
```bash
pip install --pre agent-framework            # 전체(코어+오케스트레이션)
pip install --pre agent-framework-azure-ai   # Azure/Foundry 통합 포함 권장
pip install httpx python-dotenv
```

---

## 2. 아키텍처

### 2.1 논리 구성
```
[Chat UI / Console]
        │  사용자 발화
        ▼
[Coordinator Agent] ── 핫스팟 매핑 → 병렬 호출 ──┐
        │ (agent-as-tool)                         │
        ├──> [RouteAgent]  -- tool: get_road_traffic(area) --┐
        └──> [ParkingAgent]-- tool: get_parking_status(area)-┤
                                                              ▼
                                            [SeoulCityDataClient] (httpx)
                                                              ▼
                                   서울 citydata API (지역명 기준 단일 호출)
```

- 두 도구는 동일 upstream(citydata)을 호출하되 **다른 섹션**을 추출: 주차=`PRK_STTS`, 교통=`ROAD_TRAFFIC_STTS`.
- 도구는 **MCP 없이 in-process Python 함수**로 구현(MAF의 function tool). 추후 MCP 서버로 분리 가능(현재 .NET MCP는 HDK 폴더에 별도 존재, 홀드).

### 2.2 프로젝트 구조 (제안)
```
HDK_MS/
├── .venv/                       # 가상환경 (생성됨)
├── .env                         # SEOUL_API_KEY, LLM 엔드포인트 (커밋 금지)
├── .env.sample                  # 키 목록 템플릿
├── requirements.txt
├── agent.md / prd.md / trd.md   # 컨셉 문서 (본 세트)
└── src/
    ├── config.py                # 환경변수 로드
    ├── clients/
    │   └── seoul_citydata.py    # citydata httpx 호출 + 섹션 추출
    ├── tools/
    │   ├── parking.py           # get_parking_status(area)  -> PRK_STTS 요약
    │   └── traffic.py           # get_road_traffic(area)     -> ROAD_TRAFFIC_STTS 요약
    ├── agents/
    │   ├── parking_agent.py     # ParkingAgent (persona+guardrail+tool)
    │   ├── route_agent.py       # RouteAgent
    │   └── coordinator.py       # Coordinator (두 에이전트를 도구로 종합)
    ├── hotspots.py              # 핫스팟 목록 + 목적지→핫스팟 매핑 헬퍼
    └── main.py                  # 진입점(콘솔 챗 루프)
```

---

## 3. 외부 인터페이스 — 서울 citydata
- 요청: `GET {BASE}/{API_KEY}/json/citydata/{START}/{END}/{지역명}`
  - `BASE` 기본 `http://openapi.seoul.go.kr:8088`
- 응답(JSON): 루트 `CITYDATA` 하위에 다수 섹션.
  - 주차 `PRK_STTS[]`: 주차장명/총면수/현재주차/갱신시각/요금 등 (필드명 매뉴얼로 확정)
  - 도로 `ROAD_TRAFFIC_STTS`: 종합(소통지수/평균속도/메시지) + 구간별 상태/속도
- **방어적 파싱**: 후보 키 fallback + 누락 시 None. 필드명은 `실시간도시데이터 매뉴얼.pdf`로 검증.

---

## 4. 도구(Function Tool) 스펙
| 도구 | 시그니처 | 반환 |
|------|----------|------|
| `get_parking_status` | `(area: str) -> list[dict]` | `{name, capacity, current, available, fee, updated_at}` |
| `get_road_traffic` | `(area: str, max_segments: int=8) -> dict` | `{summary:{idx, speed, msg}, segments:[{road, idx, speed}]}` |

- 가드레일(§AGENT.md): 수치는 도구 결과만, 빈 응답 시 "데이터 없음" 명시, 갱신시각 포함.
- 구조화 출력(structured output)으로 LLM이 파싱하기 쉬운 형태 반환 권장.

---

## 5. 에이전트/오케스트레이션 구현 노트
- 각 전문가: `ChatAgent`(MAF) + persona instructions(AGENT.md) + 해당 function tool 1개.
- Coordinator: ParkingAgent/RouteAgent를 **agent-as-tool**로 등록 → 병렬 호출 후 종합. (MAF의 agent→tool 변환 API 사용)
- 핫스팟 매핑: `hotspots.py`에서 사전 매핑/유사도 매칭. 매핑 결과(확정 지역명)를 전문가에 전달.

---

## 6. 설정 / 환경변수 (.env)
| 키 | 용도 |
|----|------|
| `SEOUL_API_KEY` | 서울 citydata 인증키 (필수) |
| `SEOUL_BASE_URL` | 기본 `http://openapi.seoul.go.kr:8088` |
| `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_DEPLOYMENT` | Azure OpenAI 사용 시 |
| `FOUNDRY_PROJECT_ENDPOINT` / `FOUNDRY_MODEL` | Microsoft Foundry 사용 시 |
| (대안) `GITHUB_TOKEN` | GitHub Models 사용 시 |

`.env.sample`을 커밋하고 실제 `.env`는 `.gitignore` 처리.

---

## 7. 실행 (로컬)
```bash
HDK_MS/.venv/Scripts/python -m src.main      # Windows
# 또는 venv 활성화 후: python -m src.main
```

## 8. 배포 (옵션)
- 콘솔/Chainlit 앱을 컨테이너화 → Azure Container Apps(`azd up`). 해커톤 데모는 로컬 실행으로 충분.

## 9. 빌드/호환 유의사항
- 현재 venv는 **Python 3.14.0** + **`agent-framework` 1.9.0** 설치 완료·임포트 정상(실험적 기능 경고만, 에러 없음).
  - 동반 설치: agent-framework-foundry 1.8.2, agent-framework-openai 1.8.2, agent-framework-orchestrations 1.0.0, azure-ai-projects 2.2.0, openai 2.43.0, httpx 0.28.1, pydantic 2.14.0a1 등.
- 만약 다른 머신에서 휠 충돌 시 Python 3.12/3.13로 venv 재생성(`py -3.12 -m venv .venv`).
- 설치 검증: `python -c "import agent_framework; print(agent_framework.__version__)"` → `1.9.0`.

## 10. 테스트
- 도구 단위: 실 키로 `get_parking_status`/`get_road_traffic` 호출 → citydata 파싱·필드 매핑 검증.
- 통합: 핫스팟 질의 → 종합 추천에 주차+교통+갱신시각 포함, 환각 0 확인.
- KPI 측정(PRD §4): 응답지연 P95, 실데이터 응답률, 추천 채택률(데모 수동 집계).

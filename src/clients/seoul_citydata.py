"""서울 실시간 도시데이터(citydata, OA-21285) 클라이언트.

한 번의 호출로 지역(핫스팟)별 인구/도로소통/주차/날씨 등이 모두 반환된다.
여기서는 주차(PRK_STTS)와 도로소통(ROAD_TRAFFIC_STTS) 섹션만 추출한다.

요청 형식:
    {BASE}/{API_KEY}/json/citydata/{START}/{END}/{지역명}

⚠️ citydata 필드명은 버전에 따라 다를 수 있어 후보 키(fallback)로 방어적으로 읽는다.
   실제 응답과 다르면 "실시간도시데이터 매뉴얼.pdf" 로 확정할 것.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from src.config import Settings, get_settings


# ---------- 방어적 JSON 헬퍼 ----------
def _str(node: Any, *keys: str) -> str | None:
    if not isinstance(node, dict):
        return None
    for key in keys:
        value = node.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


def _num(node: Any, *keys: str) -> float | None:
    raw = _str(node, *keys)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _int(node: Any, *keys: str) -> int | None:
    value = _num(node, *keys)
    return int(value) if value is not None else None


def _array(node: Any, *keys: str) -> list[dict] | None:
    if not isinstance(node, dict):
        return None
    for key in keys:
        value = node.get(key)
        if isinstance(value, list):
            return value
        # 한 단계 더 감싸진 경우 (예: SECTION -> {row: [...]})
        if isinstance(value, dict):
            for inner in value.values():
                if isinstance(inner, list):
                    return inner
    return None


# ---------- 호출 ----------
async def get_city_data(area: str, settings: Settings | None = None) -> dict | None:
    """지역명으로 citydata 를 호출하고 CITYDATA 노드를 반환한다."""
    settings = settings or get_settings()
    settings.require_seoul()

    url = f"{settings.seoul_base_url}/{settings.seoul_api_key}/json/citydata/1/5/{quote(area)}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    # 보통 CITYDATA 로 감싸져 있고, 실패 시 루트에 RESULT 코드가 온다.
    return data.get("CITYDATA") or data


# ---------- 섹션 추출 ----------
def extract_parking(city: dict | None) -> list[dict]:
    """PRK_STTS → [{name, capacity, current, available, fee, rates, updated_at}]"""
    lots = _array(city, "PRK_STTS")
    if not lots:
        return []

    result: list[dict] = []
    for lot in lots:
        capacity = _int(lot, "CPCTY", "TPKCT")                  # 총 주차면
        current = _int(lot, "CUR_PRK_CNT", "NOW_PRK_VHCL_CNT")  # 현재 주차 대수 (실시간 미제공 시 빈 값)
        available = max(0, capacity - current) if capacity is not None and current is not None else None

        name = _str(lot, "PRK_NM", "PKLT_NM") or "(이름 미상)"
        address = _str(lot, "ADDRESS", "ADDR", "ROAD_ADDR")
        # 전화번호: citydata 에는 없으나, 공영주차장 API 등에서 들어오면 자동 사용.
        phone = _str(lot, "TEL", "TELNO", "PHONE", "PRK_TEL")

        result.append(
            {
                "name": name,
                "type": _str(lot, "PRK_TYPE"),                  # 예: BS(부설), NS(노상) 등
                "capacity": capacity,
                "current": current,
                "available": available,
                "realtime": _str(lot, "CUR_PRK_YN") == "Y",     # 실시간 잔여 제공 여부
                "fee": _str(lot, "PAY_YN", "PAY_YN_NM"),
                "rates": _str(lot, "RATES", "PRK_CRG"),
                "updated_at": _str(lot, "CUR_PRK_TIME", "NOW_PRK_VHCL_UPDT_TM"),
                "address": address,
                "lat": _num(lot, "LAT"),
                "lng": _num(lot, "LNG"),
                "phone": phone,
                "naver_url": naver_map_url(name, address),      # 네이버 지도/앱 링크
            }
        )
    return result


def naver_map_url(name: str, address: str | None) -> str:
    """네이버 지도 검색 링크. 모바일에서는 네이버 지도 앱으로 열린다."""
    query = f"{name} {address}".strip() if address else name
    return "https://map.naver.com/p/search/" + quote(query)


def extract_traffic(city: dict | None, max_segments: int = 8) -> dict:
    """ROAD_TRAFFIC_STTS → {summary:{idx, speed, msg}, segments:[{road, idx, speed}]}"""
    road = city.get("ROAD_TRAFFIC_STTS") if isinstance(city, dict) else None
    if not isinstance(road, dict):
        return {"summary": None, "segments": []}

    avg = road.get("AVG_ROAD_DATA") if isinstance(road.get("AVG_ROAD_DATA"), dict) else road
    summary = {
        "idx": _str(avg, "ROAD_TRAFFIC_IDX", "IDX"),
        "speed": _num(avg, "ROAD_TRAFFIC_SPD", "SPD"),
        "msg": _str(avg, "ROAD_MSG", "ROAD_TRAFFIC_MSG"),
    }

    links = _array(road, "ROAD_TRAFFIC_STTS", "ROAD_TRAFFIC_STTS_LIST") or []
    segments: list[dict] = []
    for link in links[:max_segments]:
        segments.append(
            {
                "road": _str(link, "ROAD_NM", "LINK_NM") or "(구간 미상)",
                "from": _str(link, "START_ND_NM", "ST_NM"),
                "to": _str(link, "END_ND_NM", "ED_NM"),
                "idx": _str(link, "IDX", "ROAD_TRAFFIC_IDX"),
                "speed": _num(link, "SPD", "ROAD_TRAFFIC_SPD"),
            }
        )

    return {"summary": summary, "segments": segments}

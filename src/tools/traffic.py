"""교통 도구 — citydata ROAD_TRAFFIC_STTS 를 요약해 반환하는 @tool 함수.

가드레일(AGENT.md): citydata 한계상 '상대적으로 원활한 접근' 수준까지만. 정밀 경로 단정 금지.
"""

from __future__ import annotations

from agent_framework import tool

from src.clients import seoul_citydata


@tool(
    name="get_road_traffic",
    description=(
        "서울 핫스팟 지역명(예: '강남역', '여의도')의 실시간 도로소통 현황을 조회한다. "
        "종합 소통상태(원활/서행/정체)·평균속도와 구간별 상태/속도를 반환한다."
    ),
)
async def get_road_traffic(area: str, max_segments: int = 8) -> str:
    """area: 서울 핫스팟 지역명(한국어). max_segments: 구간 최대 개수."""
    city = await seoul_citydata.get_city_data(area)
    traffic = seoul_citydata.extract_traffic(city, max_segments=max_segments)

    summary = traffic["summary"]
    segments = traffic["segments"]

    if not summary or (summary.get("idx") is None and summary.get("speed") is None):
        if not segments:
            return f"'{area}' 의 실시간 도로소통 데이터를 찾지 못했습니다. (유효한 서울 핫스팟 지역명인지 확인)"

    lines = []
    if summary:
        spd = f"{summary['speed']:.0f}km/h" if summary.get("speed") is not None else "?"
        head = f"[{area} 종합] 소통:{summary.get('idx') or '?'}, 평균속도:{spd}"
        if summary.get("msg"):
            head += f" | {summary['msg']}"
        lines.append(head)

    for seg in segments:
        spd = f"{seg['speed']:.0f}km/h" if seg.get("speed") is not None else "?"
        section = f" ({seg['from']}→{seg['to']})" if seg.get("from") and seg.get("to") else ""
        lines.append(f"- {seg['road']}{section}: {seg.get('idx') or '?'}, {spd}")

    return "\n".join(lines) if lines else f"'{area}' 도로소통 데이터가 비어 있습니다."

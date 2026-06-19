"""주차 도구 — citydata PRK_STTS 를 요약해 반환하는 @tool 함수.

가드레일(AGENT.md): 수치는 citydata 결과만 사용. 데이터 없으면 '없음'을 명시.
"""

from __future__ import annotations

from agent_framework import tool

from src.clients import seoul_citydata


@tool(
    name="get_parking_status",
    description=(
        "서울 핫스팟 지역명(예: '강남역', '여의도')의 실시간 주차장 현황을 조회한다. "
        "주차장별 총 주차면/현재 주차/여유면/요금/갱신시각을 반환한다."
    ),
)
async def get_parking_status(area: str) -> str:
    """area: 서울 핫스팟 지역명(한국어)."""
    city = await seoul_citydata.get_city_data(area)
    lots = seoul_citydata.extract_parking(city)

    if not lots:
        return f"'{area}' 의 실시간 주차 데이터를 찾지 못했습니다. (유효한 서울 핫스팟 지역명인지 확인)"

    # 실시간 잔여 제공 + 여유 많은 순으로 우선 정렬
    realtime = [l for l in lots if l["realtime"] and l["available"] is not None]
    realtime.sort(key=lambda l: l["available"], reverse=True)
    others = [l for l in lots if l not in realtime]

    lines = [
        f"[{area}] 실시간 주차 현황 (주차장 {len(lots)}곳, 실시간 잔여 제공 {len(realtime)}곳)"
    ]

    if realtime:
        lines.append("· 실시간 잔여 제공 주차장 (여유 많은 순):")
        for lot in realtime[:10]:
            lines.append(
                f"  - {_name_link(lot)}: 총 {lot['capacity']}면, 현재 {lot['current']}대, "
                f"여유 {lot['available']}면 | 요금:{lot['fee'] or '?'}({lot['rates'] or '?'}) "
                f"| 갱신:{lot['updated_at'] or '?'}{_phone_link(lot)}"
            )
    else:
        lines.append("· 이 지역은 실시간 잔여면수를 제공하는 주차장이 없습니다(아래는 위치/요금 정보만).")

    # 실시간 미제공 주차장은 용량/요금/주소만 일부 안내
    if others:
        lines.append("· 그 외 주차장(실시간 잔여 미제공, 총면수/요금 기준):")
        for lot in others[:8]:
            cap = lot["capacity"] if lot["capacity"] is not None else "?"
            lines.append(
                f"  - {_name_link(lot)}: 총 {cap}면 | 요금:{lot['fee'] or '?'}({lot['rates'] or '?'})"
                f"{' | ' + lot['address'] if lot['address'] else ''}{_phone_link(lot)}"
            )

    lines.append(
        "\n(각 주차장 이름을 누르면 네이버 지도로 열립니다. 답변에 이 링크들을 그대로 유지하세요.)"
    )
    return "\n".join(lines)


def _name_link(lot: dict) -> str:
    """주차장 이름을 네이버 지도 링크가 걸린 마크다운으로."""
    if lot.get("naver_url"):
        return f"[{lot['name']}]({lot['naver_url']})"
    return lot["name"]


def _phone_link(lot: dict) -> str:
    """전화번호가 있으면 tel: 링크 추가(없으면 빈 문자열)."""
    phone = lot.get("phone")
    if not phone:
        return ""
    tel = phone.replace("-", "").replace(" ", "")
    return f" | [📞 전화]({'tel:' + tel})"

"""데이터 계층 스모크 테스트 — LLM 없이 citydata 가 실제로 나오는지 확인.

실행 (HDK_MS 에서):
    .venv\\Scripts\\python -m scripts.smoke_citydata 강남역
"""

from __future__ import annotations

import asyncio
import sys

from src.clients import seoul_citydata


async def main(area: str) -> None:
    print(f"# citydata 호출: {area}")
    city = await seoul_citydata.get_city_data(area)
    if not isinstance(city, dict):
        print("응답이 dict 가 아닙니다:", type(city), city)
        return

    print("\n## 최상위 키:", list(city.keys())[:20])

    parking = seoul_citydata.extract_parking(city)
    print(f"\n## 주차장 {len(parking)}곳")
    for lot in parking[:5]:
        print("  -", lot)

    traffic = seoul_citydata.extract_traffic(city)
    print("\n## 도로소통 종합:", traffic["summary"])
    for seg in traffic["segments"][:5]:
        print("  -", seg)


if __name__ == "__main__":
    area = sys.argv[1] if len(sys.argv) > 1 else "강남역"
    asyncio.run(main(area))

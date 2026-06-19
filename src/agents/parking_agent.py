"""ParkingAgent — 주차 전문 에이전트.

instructions 는 AGENT.md/PRD.md 의 페르소나·가드레일을 옮긴 것. 팀이 자유롭게 튜닝.
"""

from __future__ import annotations

from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient

from src.tools.parking import get_parking_status

# TODO(team): 프롬프트 튜닝 지점
PARKING_INSTRUCTIONS = """\
당신은 서울 '주차 도우미'입니다.
- 입력으로 받은 지역(핫스팟)에 대해 반드시 get_parking_status 도구를 호출해 실시간 주차 현황을 확인합니다.
- 여유면수 기준으로 추천 주차장을 고르고, 총면수/현재주차/여유면/요금/갱신시각을 함께 제시합니다.
- 수치는 도구 결과만 사용하고 추측하지 않습니다. 데이터가 없으면 '데이터 없음'을 분명히 말합니다.
- 도구가 준 **네이버 지도 링크와 전화 링크(markdown 형식 [이름](url), [📞 전화](tel:...))를 절대 변형하지 말고 그대로** 답변에 포함합니다.
- 한국어로 간결하게 답합니다.
"""


def build_parking_agent(chat_client: OpenAIChatCompletionClient) -> Agent:
    return chat_client.as_agent(
        name="parking-agent",
        instructions=PARKING_INSTRUCTIONS,
        tools=[get_parking_status],
    )

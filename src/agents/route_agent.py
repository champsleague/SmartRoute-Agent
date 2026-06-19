"""RouteAgent — 실시간 도로소통/접근 전문 에이전트.

instructions 는 AGENT.md/PRD.md 의 페르소나·가드레일을 옮긴 것. 팀이 자유롭게 튜닝.
"""

from __future__ import annotations

from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient

from src.tools.traffic import get_road_traffic

# TODO(team): 프롬프트 튜닝 지점
ROUTE_INSTRUCTIONS = """\
당신은 서울 '교통 분석가'입니다. 추천 주차장이 있는 지역까지의 '접근 소통'을 분석합니다.
- 입력으로 받은 지역(핫스팟)에 대해 반드시 get_road_traffic 도구를 호출해 실시간 소통을 확인합니다.
- 소통상태(원활/서행/정체)·평균속도·구간별 상태로 '그 지역으로 진입할 때 어느 방향/구간이 상대적으로 원활한지'를 설명합니다.
- citydata 한계상 정밀 경로(턴바이턴)는 단정하지 않습니다. '지역 접근 소통' 수준으로만 안내합니다.
- 수치는 도구 결과만 사용합니다. 한국어로 간결하게 답합니다.
"""


def build_route_agent(chat_client: OpenAIChatCompletionClient) -> Agent:
    return chat_client.as_agent(
        name="route-agent",
        instructions=ROUTE_INSTRUCTIONS,
        tools=[get_road_traffic],
    )

"""SmartRoute — Chainlit 챗 UI.

실행 (HDK_MS 에서):
    .venv\\Scripts\\chainlit run app.py -w
    # 또는: .venv\\Scripts\\python -m chainlit run app.py -w
브라우저가 http://localhost:8000 으로 열린다.
"""

from __future__ import annotations

import chainlit as cl

from src.agents.coordinator import build_coordinator
from src.llm import build_chat_client

WELCOME = (
    "안녕하세요! **SmartRoute** 입니다. 🚗\n\n"
    "서울 목적지를 알려주시면 **실시간 도로소통**과 **주차 가능 현황**을 함께 안내해 드려요.\n\n"
    "예) `여의도 IFC몰 가는 길이랑 주차 알려줘`"
)


@cl.on_chat_start
async def on_chat_start() -> None:
    # 대화 세션마다 코디네이터 + 메모리 세션을 1개씩 둔다 (맥락 유지).
    coordinator = build_coordinator(build_chat_client())
    session = coordinator.create_session()
    cl.user_session.set("coordinator", coordinator)
    cl.user_session.set("session", session)

    await cl.Message(content=WELCOME).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    coordinator = cl.user_session.get("coordinator")
    session = cl.user_session.get("session")

    # 응답 대기 동안 Chainlit 이 로딩 표시를 보여준다.
    response = await coordinator.run(message.content, session=session)
    await cl.Message(content=response.text or "(응답 없음)").send()

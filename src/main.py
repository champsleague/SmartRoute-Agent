"""SmartRoute 콘솔 챗 진입점.

실행 (HDK_MS 디렉터리에서):
    .venv\\Scripts\\python -m src.main      # Windows
    python -m src.main                       # venv 활성화 후
"""

from __future__ import annotations

import asyncio

from src.agents.coordinator import build_coordinator
from src.llm import build_chat_client


async def main() -> None:
    chat_client = build_chat_client()
    coordinator = build_coordinator(chat_client)

    # 하나의 세션으로 대화 맥락(이전 목적지/의도)을 유지한다.
    session = coordinator.create_session()

    print("=" * 60)
    print(" SmartRoute — 서울 실시간 주차/교통 안내")
    print(" 예) '강남역 가는 빠른 길이랑 주차 알려줘'   (종료: exit)")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n질문> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            break

        response = await coordinator.run(user_input, session=session)
        print("\n" + (response.text or "(응답 없음)"))


if __name__ == "__main__":
    asyncio.run(main())

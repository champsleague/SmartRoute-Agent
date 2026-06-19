"""Azure OpenAI 챗 클라이언트 팩토리.

ChatCompletions API 기반 클라이언트(OpenAIChatCompletionClient)를 사용한다.
- azure_endpoint 를 주면 Azure OpenAI 로 라우팅된다.
- Responses API 기반 OpenAIChatClient 는 Azure 에서 최신 preview api-version 을 요구해
  '2024-10-21' 등에서 "API version not supported" 가 나므로 사용하지 않는다.
- (별도 agent-framework-azure-ai 패키지는 코어 1.9.0 과 버전 불일치라 사용하지 않는다.)
"""

from __future__ import annotations

from agent_framework.openai import OpenAIChatCompletionClient

from src.config import Settings, get_settings


def build_chat_client(settings: Settings | None = None) -> OpenAIChatCompletionClient:
    settings = settings or get_settings()
    settings.require_azure()

    return OpenAIChatCompletionClient(
        model=settings.azure_openai_deployment,      # Azure 배포 이름
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )

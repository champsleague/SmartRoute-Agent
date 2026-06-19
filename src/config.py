"""환경설정 로드 (.env). 모든 키/엔드포인트를 한 곳에서 관리한다."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# HDK_MS/.env 를 읽는다 (없으면 환경변수만 사용).
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # 서울 실시간 도시데이터(citydata, OA-21285)
    seoul_api_key: str
    seoul_base_url: str

    # Azure OpenAI (LLM 두뇌)
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_deployment: str   # Azure 포털의 "배포 이름" (예: gpt-4o)
    azure_openai_api_version: str

    def require_seoul(self) -> None:
        if not self.seoul_api_key:
            raise RuntimeError("SEOUL_API_KEY 가 설정되지 않았습니다 (.env 확인).")

    def require_azure(self) -> None:
        missing = [
            name
            for name, value in {
                "AZURE_OPENAI_ENDPOINT": self.azure_openai_endpoint,
                "AZURE_OPENAI_API_KEY": self.azure_openai_api_key,
                "AZURE_OPENAI_DEPLOYMENT": self.azure_openai_deployment,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Azure OpenAI 설정 누락: {', '.join(missing)} (.env 확인).")


def get_settings() -> Settings:
    return Settings(
        seoul_api_key=os.getenv("SEOUL_API_KEY", ""),
        seoul_base_url=os.getenv("SEOUL_BASE_URL", "http://openapi.seoul.go.kr:8088").rstrip("/"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )

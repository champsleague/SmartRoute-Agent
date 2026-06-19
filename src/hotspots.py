"""목적지(자연어) → 서울 citydata 핫스팟 지역명 매핑 헬퍼.

citydata 는 임의 주소가 아니라 서울 ~121개 '핫스팟 지역명' 기준으로 동작한다.
아래는 대표 샘플 목록 — 전체 목록은 "실시간도시데이터 매뉴얼.pdf" 에서 보강할 것.
정교한 매핑은 Coordinator(LLM)가 담당하고, 이 모듈은 검증/후보 제시용 보조 도구다.
"""

from __future__ import annotations

# 대표 핫스팟 샘플 (정확한 표기는 매뉴얼 기준으로 보강 필요)
SUPPORTED_AREAS: list[str] = [
    "강남역", "역삼역", "신논현역·논현역", "교대역", "고속터미널역",
    "여의도", "여의도공원", "영등포 타임스퀘어",
    "광화문·덕수궁", "경복궁", "시청광장",
    "홍대 관광특구", "연남동", "신촌·이대역",
    "잠실 관광특구", "잠실종합운동장", "잠실한강공원",
    "성수카페거리", "건대입구역", "동대문 관광특구",
    "명동 관광특구", "이태원 관광특구", "남대문시장",
    "강남 MICE 관광특구", "코엑스", "가로수길",
]


def normalize(text: str) -> str:
    return "".join(text.split()).lower()


def resolve_hotspot(text: str) -> str | None:
    """입력 텍스트에 가장 단순하게 매칭되는 핫스팟을 반환(없으면 None)."""
    if not text:
        return None
    key = normalize(text)
    # 1) 정확/부분 일치
    for area in SUPPORTED_AREAS:
        if normalize(area) in key or key in normalize(area):
            return area
    return None


def candidates(text: str, limit: int = 3) -> list[str]:
    """간단한 후보 추천(부분 토큰 일치). 매핑 실패 시 사용자에게 제시."""
    key = normalize(text)
    scored = [(area, len(set(key) & set(normalize(area)))) for area in SUPPORTED_AREAS]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [area for area, _ in scored[:limit]]

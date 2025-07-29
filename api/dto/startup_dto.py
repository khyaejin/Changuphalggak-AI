from pydantic import BaseModel
from typing import List

# 창업 아이디어 요청 Request 예시
class StartupRequestDTO(BaseModel):
    idea_description: str  # 창업 아이디어 설명 (사용자가 직접 입력)
    industry_type: str     # 산업 종류
    funding_amount: int    # 필요한 예상 자금 (ex. 난 300만원정도 필요해, 난 1000만원 이상의 지원이 필요해! 등)

# 추천 사업 응답 데이터 구조
class StartupResponseDTO(BaseModel):
    recommended_documents: List[str]  # 추천된 창업 사업 목록 (상위 3개 반환 예정)

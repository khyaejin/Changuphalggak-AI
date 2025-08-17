from pydantic import BaseModel
from typing import List

# 창업 지원 사업 추천 Request
class StartupRequestDTO(BaseModel):
    idea_title: str  # 창업 아이디어 제목 (사용자가 직접 입력)
    idea_description: str  # 창업 아이디어 설명 (사용자가 직접 입력)

# 창업 지원 사업 추천 Response (List로 반환 예정)
class SimilarSupportDTO(BaseModel):
    external_ref: str
    score: float  # 코사인 유사도(내적값)

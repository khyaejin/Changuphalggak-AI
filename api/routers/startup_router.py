from typing import List

from fastapi import APIRouter, Query

from api.dto.startup_dto import CreateStartupResponseDTO, StartupSupportSyncRequest
from api.services.startup_fetch_service import fetch_startup_supports_async
from api.dto.recommended_dto import StartupRequestDTO, SimilarSupportDTO
from api.services.recommend_service import similar_top_k

router = APIRouter()

# 창업 지원 사업 수집
@router.post("/api/startup-supports", response_model=List[CreateStartupResponseDTO])
async def get_startup_supports(
        req: StartupSupportSyncRequest,
        hard_max_pages: int = Query(100, ge=1, le=500)  # 기본값 100
) -> List[CreateStartupResponseDTO]:
    return await fetch_startup_supports_async(
        after_external_ref=req.after_external_ref,
        hard_max_pages=hard_max_pages
    )

# 창업 지원 사업 유사도 검색 상위 3개 반환 API
@router.post("/api/similar", response_model=List[SimilarSupportDTO])
def get_similar_supports(payload: StartupRequestDTO, k: int = Query(30, ge=1, le=100)):
    """
    아이디어(제목+설명)를 입력 받아 코사인 유사도 상위 k개의 지원사업을 반환(디폴트 30개)
    """
    return similar_top_k(payload, k=k)
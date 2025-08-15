from typing import List

from fastapi import APIRouter, HTTPException

from api.dto.startup_dto import CreateStartupResponseDTO
from api.services.startup_service import get_startup_supports

router = APIRouter()
@router.post("/api/startup-supports", response_model=List[CreateStartupResponseDTO])
async def get_startup_supports():
    return await get_startup_supports()


# 창업 사업 추천 상위 3개 반환 API

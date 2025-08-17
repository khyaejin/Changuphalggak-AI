from typing import List

from fastapi import APIRouter

from api.dto.startup_dto import CreateStartupResponseDTO, StartupSupportSyncRequest
from api.services.startup_fetch_service import fetch_startup_supports_async

router = APIRouter()
@router.post("/api/startup-supports", response_model=List[CreateStartupResponseDTO])
async def get_startup_supports(req: StartupSupportSyncRequest) -> List[CreateStartupResponseDTO]:
    return await fetch_startup_supports_async(after_external_ref=req.after_external_ref)

# 창업 사업 추천 상위 3개 반환 API

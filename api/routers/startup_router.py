from fastapi import APIRouter, HTTPException
from api.services.startup_service import get_recommended_documents
from api.dto.startup_dto import StartupRequestDTO, StartupResponseDTO

router = APIRouter()

# 창업 사업 추천 상위 3개 반환 API
@router.post("api/startup/recommended-supports", response_model=StartupResponseDTO)
async def recommend_documents(request: StartupRequestDTO):
    try:
        # 서비스에서 추천 사업 목록을 받아옴
        recommended_documents = get_recommended_documents(request)
        return recommended_documents
    except Exception as e:
        # 오류 발생 시 HTTP 500 상태 코드와 함께 오류 메시지 반환

        # TODO: 이후 적절한 여러 예외처리 필요
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

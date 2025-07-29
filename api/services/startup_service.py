from api.dto.startup_dto import StartupRequestDTO, StartupResponseDTO
from models.ai_model.recommended_doc_ai_model import load_model, get_recommended_documents_from_ai

def get_recommended_documents(request_data: StartupRequestDTO) -> StartupResponseDTO:
    # AI 모델 로드
    model = load_model()

    # AI 모델을 사용해 추천 지원 사업 목록 얻기
    recommended_documents = get_recommended_documents_from_ai(model, request_data.idea_description)

    # 응답 데이터 구조로 반환 (예시)
    return StartupResponseDTO(recommended_documents=recommended_documents)

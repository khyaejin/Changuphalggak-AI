from typing import List
from fastapi import APIRouter, Query

from api.dto.startup_dto import CreateStartupResponseDTO, StartupSupportSyncRequest
from api.services.startup_fetch_service import fetch_startup_supports_async
from api.dto.recommended_dto import StartupRequestDTO, SimilarSupportDTO
from api.services.recommend_service import similar_top_k

# ===== 디버깅용 로거 =====
import logging, json, time
logger = logging.getLogger("startup_service")

def _safe_dump(obj):
    try:
        # v2
        return obj.model_dump(mode="json")
    except AttributeError:
        # v1
        try:
            return obj.dict()
        except AttributeError:
            try:
                return json.loads(obj.json())
            except Exception:
                # 최후의 보루: 문자열로라도 살려서 찍기
                return str(obj)

def _preview_list(items, n=3):
    """응답 리스트 미리보기(상위 n개), JSON 직렬화 안전"""
    try:
        preview = [_safe_dump(i) for i in items[:n]]
        return json.dumps(preview, ensure_ascii=False, indent=2)
    except Exception as e:
        # 로깅 실패해도 API는 절대 죽지 않게
        return f"<preview serialization failed: {e}>"

router = APIRouter()

# 창업 지원 사업 수집
@router.post("/ai/startup-supports", response_model=List[CreateStartupResponseDTO])
async def get_startup_supports(
        req: StartupSupportSyncRequest,
        hard_max_pages: int = Query(100, ge=1, le=300)  # 기본값 100
) -> List[CreateStartupResponseDTO]:
    #  요청 파라미터 찍기
    logger.info(
        "[지원사업수집] afterExternalRef=%s expiredExternalRefs.len=%s hard_max_pages=%s",
        req.after_external_ref,
         len(req.expired_external_refs),
        hard_max_pages,
    )

    t0 = time.perf_counter()
    result = await fetch_startup_supports_async(
        after_external_ref=req.after_external_ref,
        expired_external_refs=req.expired_external_refs,
        hard_max_pages=hard_max_pages
    )
    dt = (time.perf_counter() - t0) * 1000

    # 반환 직전 프리뷰 보기
    logger.info("[지원사업수집] fetched=%d, elapsed=%.1fms", len(result), dt)
    try:
        logger.debug("[지원사업수집] preview(3)=%s", _preview_list(result, n=3))
    except Exception as e:
        logger.warning("[지원사업수집] preview log failed: %s", e)

    return result

# 창업 지원 사업 유사도 검색 상위 3개 반환 API
@router.post("/ai/similar", response_model=List[SimilarSupportDTO])
def get_similar_supports(payload: StartupRequestDTO, k: int = Query(30, ge=1, le=100)):
    """
    아이디어(제목+설명)를 입력 받아 코사인 유사도 상위 k개의 지원사업을 반환(디폴트 30개)
    """
    # 요청 페이로드 찍기
    try:
        title = getattr(payload, "idea_title", None)
        logger.info("[similar] k=%d, title='%s'", k, title)
        # 전체 페이로드 보고싶을 때:
        logger.debug("[similar] payload=%s", json.dumps(_safe_dump(payload), ensure_ascii=False))
    except Exception as e:
        logger.warning("[similar] payload log failed: %s", e)

    t0 = time.perf_counter()
    result = similar_top_k(payload, k=k)
    dt = (time.perf_counter() - t0) * 1000

    # 반환 직전 보기
    logger.info("[similar] result_count=%d, elapsed=%.1fms", len(result), dt)
    try:
        logger.debug("[similar] preview(3)=%s", _preview_list(result, n=3))
    except Exception as e:
        logger.warning("[similar] preview log failed: %s", e)

    return result

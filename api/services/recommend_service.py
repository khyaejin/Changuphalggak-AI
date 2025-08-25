# 창업 지원사업 추천 로직
import os
import logging
from typing import List

from api.dto.recommended_dto import StartupRequestDTO, SimilarSupportDTO
from api.embedding.vectorizer import embed_texts
from api.embedding.index_singleton import get_store 

logger = logging.getLogger("startup_recommender")

INDEX_PATH = os.getenv("INDEX_PATH", "data/supports.faiss")

def similar_top_k(req: StartupRequestDTO, k: int = 30) -> List[SimilarSupportDTO]:
    """
    아이디어 제목+설명을 합쳐 임베딩 → FAISS에서 상위 k개 검색
    """
    title = (req.idea_title or "").strip()
    desc  = (req.idea_description or "").strip()
    query = (title + " " + desc).strip()

    if not query:
        logger.warning("[유사도] 요청 텍스트가 비어 있어 유사도 계산을 건너뜁니다.")
        return []

    # 쿼리 임베딩 (1, d) - L2 정규화된 float32
    qv = embed_texts([query])

    # 싱글톤 인덱스 로드
    store = get_store()
    if store.is_empty():
        logger.warning("[유사도] 색인된 데이터가 없음")
        return []
    # 벡터 검색 → 상위 k개 결과 반환
    # 결과 형식 {"ref": , "score": , "score01": }
    hits = store.search_one(qv[0], top_k=k)

    # DTO 변환
    out: List[SimilarSupportDTO] = []
    for h in hits:
        ref = str(h.get("ref"))
        # score01(0~1)이 있으면 우선 사용, 없으면 score(-1~1)
        score = float(h["score01"]) if "score01" in h else float(h.get("score", 0.0))
        out.append(SimilarSupportDTO(external_ref=ref, score=score))
    return out

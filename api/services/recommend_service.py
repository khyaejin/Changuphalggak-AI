"""
창업 지원사업 추천 로직
"""
import os
import logging
from typing import List

from api.dto.recommended_dto import StartupRequestDTO, SimilarSupportDTO
from api.embedding.vectorizer import embed_texts, embedding_dimension
from api.embedding.faiss_store import FaissStore

logger = logging.getLogger("=== 창업 추천 로직 시작 ===")

INDEX_PATH = os.getenv("INDEX_PATH", "data/supports.faiss")
IDMAP_PATH = os.getenv("IDMAP_PATH", "data/refs.json")

def similar_top_k(req: StartupRequestDTO, k: int = 30) -> List[SimilarSupportDTO]:
    """
    아이디어 제목+설명을 합쳐 임베딩 → FAISS에서 상위 k개 검색
    k=30으로 고정해둠
    """
    title = (req.idea_title or "").strip()
    desc  = (req.idea_description or "").strip()
    query = (title + " " + desc).strip()
    # 요청 텍스트가 비어있는 경우
    if not query:
        logger.warning("[SIM] 요청 텍스트가 비어 있어 유사도 계산을 건너뜁니다.")
        return []

    # 쿼리 임베딩 (1, d)
    qv = embed_texts([query])  # float32, L2 정규화

    # 인덱스 로드
    store = FaissStore(index_path=INDEX_PATH, idmap_path=IDMAP_PATH, dim=embedding_dimension())
    store.load()
    if store.ntotal == 0:
        # 인덱스가 비어있느 경우
        logger.warning("[SIM] 색인된 데이터가 없어 검색 불가")
        return []

    # 검색
    hits = store.search(qv, k)
    # [(ref, score)] → DTO 변환
    return [SimilarSupportDTO(external_ref=ref, score=score) for ref, score in hits]

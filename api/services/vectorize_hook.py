import os
import re
import logging
from typing import List

from api.embedding.vectorizer import embed_texts, embedding_dimension
from api.embedding.faiss_store import FaissStore
from api.dto.startup_dto import CreateStartupResponseDTO

logger = logging.getLogger("vectorize_hook")

# 경로 불러오기
INDEX_PATH = os.getenv("INDEX_PATH", "data/supports.faiss")
IDMAP_PATH = os.getenv("IDMAP_PATH", "data/refs.json")

def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _norm(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()

def _build_text_from_dto(dto: CreateStartupResponseDTO) -> str:
    # 제목 + 본문만 사용
    return f"{_norm(dto.title)} {_norm(dto.support_details)}".strip()

def vectorize_and_upsert_from_dtos(dtos: List[CreateStartupResponseDTO]) -> None:
    """
    1) DTO 리스트 -> [제목+본문] 임베딩
    2) external_ref 인덱스로 사용
    """
    # 전처리 먼저) external_ref(식별자), 제목/본문이 있는 항목만 사용하도록
    valid = [d for d in dtos if d.external_ref and (d.title or d.support_details)]
    if not valid:
        logger.info("[VEC] 유효한 데이터(external_ref, 제목, 본문이 있는 데이터)가 없음")
        return

    texts = [_build_text_from_dto(d) for d in valid]
    refs  = [str(d.external_ref) for d in valid]

    dim = embedding_dimension()
    vecs = embed_texts(texts, batch_size=64)

    _ensure_dir(INDEX_PATH)
    _ensure_dir(IDMAP_PATH)

    store = FaissStore(index_path=INDEX_PATH, idmap_path=IDMAP_PATH, dim=dim)
    store.load()
    store.add_with_refs(vecs, refs)
    store.save()

    logger.info("[VEC] 새로 추가된 벡터 개수=%s, 현재 인덱스 총 개수=%s", len(refs), store.ntotal)

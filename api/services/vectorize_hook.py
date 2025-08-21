# 벡터화 및 external_ref 기반 색인 생성 로직
import os
import re
import logging
from typing import List

from api.embedding.vectorizer import embed_texts, embedding_dimension
from api.embedding.faiss_store import FaissStore
from api.dto.startup_dto import CreateStartupResponseDTO

logger = logging.getLogger("startup_service")

INDEX_PATH = os.getenv("INDEX_PATH", "data/supports.faiss")

def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def _norm(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()

def _build_text_from_dto(dto: CreateStartupResponseDTO) -> str:
    # 제목+본문만 사용
    return f"{_norm(dto.title)} {_norm(dto.support_details)}".strip()

def vectorize_and_upsert_from_dtos(dtos: List[CreateStartupResponseDTO]) -> None:
    # external_ref 있고 제목/본문 있는 것만
    valid = [d for d in dtos if d.external_ref and (d.title or d.support_details)]
    if not valid:
        logger.info("[벡터화] 유효한 데이터 없음")
        return

    texts = [_build_text_from_dto(d) for d in valid]
    refs = [str(d.external_ref) for d in valid]

    # 숫자 문자열만 남김
    keep_idx = [i for i, r in enumerate(refs) if r.isdigit()]
    if not keep_idx:
        logger.info("[벡터화] 숫자 external_ref 없음")
        return
    texts = [texts[i] for i in keep_idx]
    refs = [refs[i] for i in keep_idx]

    # 같은 ref가 여러 번 오면 마지막 것만
    last = {}
    for i, r in enumerate(refs):
        last[r] = i
    uniq_idx = sorted(last.values())
    texts = [texts[i] for i in uniq_idx]
    refs = [refs[i] for i in uniq_idx]

    dim = embedding_dimension()
    vecs = embed_texts(texts, batch_size=64).astype("float32")  # add 전에 정규화는 FaissStore가 처리

    _ensure_dir(INDEX_PATH)

    store = FaissStore(index_path=INDEX_PATH, dim=dim)
    store.load()
    store.upsert_with_external_ids(vecs, refs)  # 중복은 삭제 후 재추가
    store.save()

    logger.info("[벡터화] upsert=%d, ntotal=%d", len(refs), store.ntotal)

# FAISS 인덱스 관리 클래스
# - 코사인 유사도 기반 (코사인 = 정규화된 벡터들의 내적 값)
# - external_ref(숫자 문자열)를 int로 바꿔 ID로 사용

import os
from typing import Iterable, List, Dict, Any

import faiss
import numpy as np


class FaissStore:
    def __init__(self, index_path: str, dim: int):
        self.index_path = index_path
        self.dim = dim
        self.index: faiss.Index | None = None

    # ---------- 기본 ----------
    @property
    def ntotal(self) -> int:
        return int(self.index.ntotal) if self.index is not None else 0

    def _new_index(self) -> None:
        # 내적 기반 (코사인용) 벡터는 항상 정규화해서 넣고 검색해야 함
        base = faiss.IndexFlatIP(self.dim)
        self.index = faiss.IndexIDMap2(base)

    def load(self) -> None:
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self._new_index()

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        faiss.write_index(self.index, self.index_path)

    def clear(self) -> None:
        # 전부 비우기
        self._new_index()

    # ---------- 내부 메서드 ----------
    # 데이터 타입을 float32로 변환(FAOSS가 요규하는 형식임)
    # FAISS가 빠르고 안정적으로 읽을 수 있도록 메모리를 연속 배열로 변환
    def _normalize(self, vecs: np.ndarray) -> np.ndarray:
        return np.ascontiguousarray(vecs, dtype=np.float32)


    def _ensure_f32(self, vecs: np.ndarray) -> np.ndarray:
        return vecs.astype("float32") if vecs.dtype != np.float32 else vecs

    def _to_ids(self, refs: Iterable[str]) -> np.ndarray:
        # "174700" 같은 문자열을 int64로 변환
        return np.asarray([np.int64(int(r)) for r in refs], dtype=np.int64)

    # ---------- 추가/업서트/삭제 ----------
    def add_with_external_ids(self, vectors: np.ndarray, external_refs: List[str]) -> None:
        assert self.index is not None, "인덱스가 준비되지 않음"
        vecs = self._ensure_f32(vectors)
        assert vecs.shape[1] == self.dim, "차원 불일치"
        vecs = self._normalize(vecs)
        ids = self._to_ids(external_refs)
        self.index.add_with_ids(vecs, ids)

    def upsert_with_external_ids(self, vectors: np.ndarray, external_refs: List[str]) -> None:
        # 같은 ref가 있으면 지우고 다시 넣기
        self.remove_by_external_ids(external_refs)
        self.add_with_external_ids(vectors, external_refs)

    # external_id 기반 인덱스 제거
    def remove_by_external_ids(self, external_refs: Iterable[str]) -> int:
        assert self.index is not None, "인덱스가 준비되지 않음"
        ids = self._to_ids(external_refs)
        before = self.ntotal
        sel = faiss.IDSelectorArray(len(ids), ids) # IDSelectorArray  사용(대량 삭제 최적화를 위해)
        self.index.remove_ids(sel)
        after = self.ntotal
        return before - after

    # ---------- 검색 ----------
    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> List[List[Dict[str, Any]]]:
        """
        반환: 쿼리별 리스트
         {ref: "174700", score: float}
        score는 코사인 값(내적) 범위 대략 [-1, 1]
        """
        assert self.index is not None, "인덱스가 준비되지 않음"
        q = self._ensure_f32(query_vectors)
        assert q.shape[1] == self.dim, "차원 불일치"
        q = self._normalize(q)

        scores, ids = self.index.search(q, top_k)  # (nq, k)
        results: List[List[Dict[str, Any]]] = []
        for i in range(ids.shape[0]):
            row: List[Dict[str, Any]] = []
            for j in range(ids.shape[1]):
                _id = int(ids[i, j])
                if _id == -1:
                    continue  # 비어있을 때 -1
                row.append({"ref": str(_id), "score": float(scores[i, j])})
            results.append(row)
        return results

    def search_one(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        q = query_vector.reshape(1, -1)
        return self.search(q, top_k=top_k)[0]

    # ---------- 편의 ----------
    def count(self) -> int:
        return self.ntotal

    def is_empty(self) -> bool:
        return self.ntotal == 0

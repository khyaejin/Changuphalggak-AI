"""
벡터 인덱스 관리 클래스(FAISS 사용)
- FAISS: 유사도 검색에 최적화된 벡터 검색 라이브러리
- 숫자 ID만 관리 가능
"""
from __future__ import annotations
import json
import os
import threading
from typing import Dict, List, Tuple, Optional

import numpy as np
import faiss


class FaissStore:
    # 초기화 메서드
    def __init__(self, index_path, idmap_path, dim):
        self.index_path = index_path # 인덱스를 저장할 파일 위치
        self.idmap_path = idmap_path # ref↔id 매핑 JSON 파일 위치
        self.dim = dim  # 벡터 차원
        self._lock = threading.RLock()
        self._index = None # 실제 FAISS 인덱스 초기화
        self._ref2id = {}  # ref(문자열) → id(int64)
        self._id2ref = {} # id(int64) → ref(문자열)

    # ---------- 내부 유틸 ----------
    @staticmethod
    def _stable_int64(ref: str) -> int: # _ensure_id에서 사용
        """
        ref 문자열 -> int(64비트)
        - 문자열 -> 바이트 -> 정수
        - hash()는 값이 달라질 수 있어서 늘 같은 값을 내기 위함
        - 0은 사용 x
        """
        v = int.from_bytes(ref.encode("utf-8"), "little", signed=False)
        v &= (1 << 63) - 1  # 음수 나오지 않도록
        if v == 0:
            v = 1  # 0은 제외
        return v

    def _ensure_id(self, ref: str) -> int:
        """
        ref 문자열 -> int(64비트) 최종 메서드
        - 이미 있으면 -> 기존 거 사용
        - 없으면 -> 새로 만듦
        - 충돌 생기면 -> 비어있는 ID 찾아서 사용
        """
        if ref in self._ref2id:
            return self._ref2id[ref]
        v = self._stable_int64(ref)
        # 충돌 방지
        while v in self._id2ref and self._id2ref[v] != ref:
            v = (v + 1) & ((1 << 63) - 1)
        self._ref2id[ref] = v
        self._id2ref[v] = ref
        return v

    def _ensure_index(self):
        if self._index is None:
            # 로드에 실패하면 새 인덱스 생성
            if os.path.exists(self.index_path):
                idx = faiss.read_index(self.index_path)
                if idx.d != self.dim:
                    raise RuntimeError(f"Index dim {idx.d} != expected {self.dim}")
                #
                # 이미 IDMap으로 저장되어 있을 수도 있음
                self._index = idx
            else:
                base = faiss.IndexFlatIP(self.dim)
                self._index = faiss.IndexIDMap(base)

    def _is_idmap(self) -> bool:
        # 현재 인덱스가 IDMap 기반인가 확인
        return isinstance(self._index, faiss.IndexIDMap) or isinstance(self._index, faiss.IndexIDMap2)

    # ---------- 퍼시스턴스 ----------
    def load(self):
        """
        인덱스랑 ref <-> id 매핑 정보를 파일에서 읽어오는 메서드
        """
        with self._lock:
            self._ensure_index()
            if os.path.exists(self.idmap_path):
                with open(self.idmap_path, "r", encoding="utf-8") as f:
                    self._ref2id = json.load(f)
                # 키는 str, 값은 int
                self._ref2id = {str(k): int(v) for k, v in self._ref2id.items()}
                self._id2ref = {v: k for k, v in self._ref2id.items()}

    def save(self):
        """
        인덱스랑 ref <-> id 관계를 저장
        """
        with self._lock:
            if self._index is None:
                return
            faiss.write_index(self._index, self.index_path)
            with open(self.idmap_path, "w", encoding="utf-8") as f:
                json.dump(self._ref2id, f, ensure_ascii=False)

    # ---------- 공개 API ----------
    @property
    def ntotal(self) -> int:
        # 인덱스에 저장되어있느 벡터 개수
        with self._lock:
            self._ensure_index()
            return int(self._index.ntotal)

    def add_with_refs(self, vectors: np.ndarray, refs: List[str]) -> None:
        """
        벡터랑 ref 같이 추가
        """
        if vectors.ndim != 2 or vectors.shape[1] != self.dim:
            raise ValueError(f"vectors shape must be (n, {self.dim})")

        if len(refs) != vectors.shape[0]:
            raise ValueError("len(refs) must equal vectors.shape[0]")

        with self._lock:
            self._ensure_index()
            if not self._is_idmap():
                # IDMap이 아니면 래핑해서 사용
                self._index = faiss.IndexIDMap(self._index)

            ids = np.array([self._ensure_id(r) for r in refs], dtype="int64")

            try:
                self._index.remove_ids(ids) # 같은 ID 있으면 먼저 제거
            except Exception:
                pass

            self._index.add_with_ids(vectors, ids)

    def search(self, query_vec: np.ndarray, k: int) -> List[Tuple[str, float]]:
        """
        검색 메서드
        쿼리 벡터와 가장 비슷한 벡터 k개를 찾음 (k=3으로 진행 예정)
        return: ref(문자열), 유사도 점수 -> Springboot에 넘겨 내용 확인
        """
        if query_vec.ndim != 2 or query_vec.shape[1] != self.dim or query_vec.shape[0] != 1:
            raise ValueError(f"query_vec shape must be (1, {self.dim})")

        with self._lock:
            self._ensure_index()
            scores, ids = self._index.search(query_vec, int(k))

        res: List[Tuple[str, float]] = []
        for i, s in zip(ids[0].tolist(), scores[0].tolist()):
            if i == -1:
                continue
            ref = self._id2ref.get(int(i))
            if ref is not None:
                res.append((ref, float(s)))
        return res

    def delete_by_refs(self, refs: List[str]) -> int:
        # ref를 인덱스에서 제거하는 메서드
        with self._lock:
            self._ensure_index()
            ids = [self._ref2id.get(r) for r in refs]
            ids = [i for i in ids if i is not None]
            if not ids:
                return 0
            removed = self._index.remove_ids(np.array(ids, dtype="int64"))
            return int(removed.size) if hasattr(removed, "size") else 0

    def contains(self, ref: str) -> bool:
        # ref가 매핑 테이블에 있는지 확인
        return ref in self._ref2id

"""
FAISS를 이용해 벡터 인덱스를 관리하는 클래스
FAISS: 벡터 검색 라이브러리 (유사도 검색에 최적화)
숫자 ID만 관리 가능하기 때문에 external_ref를 숫자 ID로 관리해주어야 함
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

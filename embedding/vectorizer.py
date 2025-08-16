"""
지원 사업 공고 속 텍스트 → SBERT 임베딩 변환 로직
- 모델은 프로세스 내 싱글턴으로 로드
- 코사인 유사도 계산을 위해 L2 정규화된 벡터 반환
"""

from __future__ import annotations

import html
import re
from threading import Lock
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: Optional[SentenceTransformer] = None
_model_lock = Lock()


def load_model() -> SentenceTransformer:
    """ SBERT 모델을 한번만 로드해서 재사용하기 위해(전역변수로 사용)"""
    global _model
    if _model is None: # 아직 모델이 로드되지 않았다면
        with _model_lock: # lock 사용해 여러 스레드가 모델 초기화하지 못하게 방지(멀티 스레드 환경)
            if _model is None: # lock 잡는 사이에 다른 스레드가 모델 로드했을 수도 있음 -> 더블체크락킹 사용
                _model = SentenceTransformer(MODEL_NAME) # 모델 불러오기
    return _model


def _norm_text(x: Optional[str]) -> str:
    """간단한 전처리 진행: HTML 엔티티 제거, 공백 정리, 소문자로 변경"""
    if not x:
        return ""
    x = html.unescape(x)
    x = re.sub(r"\s+", " ", x).strip().lower()
    return x


def build_index_text(item: Dict[str, Any]) -> str:
    """
    색인용 텍스트 생성
    API 응답 Json -> 필요한 필드만 뽑아 하나의 문자열로 생성
    """
    parts = [
        item.get("biz_pbanc_nm"), # 제목
        item.get("pbanc_ctnt") # 본문
    ]
    return " ".join(_norm_text(p) for p in parts if p) # 값이 있는 필드만 사용

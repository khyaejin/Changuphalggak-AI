# 프로세스 전체에서 하나의 FaissStore만 쓰기 위해 싱글톤 패턴으로 생성
from threading import Lock
from api.embedding.faiss_store import FaissStore
from api.embedding.vectorizer import embedding_dimension
import os

INDEX_PATH = os.getenv("INDEX_PATH", "data/supports.faiss")

_store = None
_lock = Lock()

def get_store() -> FaissStore:
    global _store
    if _store is None: # 최조 1회만 생성, 이후 같은 객체 반환(싱글톤 패턴)
        with _lock: # 멀티스레드 환경에서 동시에 접근해도 안전하도록 lock 설정
            if _store is None:
                s = FaissStore(index_path=INDEX_PATH, dim=embedding_dimension())
                s.load()
                _store = s
    return _store

from api.dto.recommended_dto import StartupRequestDTO
from api.embedding import vectorizer
import api.services.recommend_service as sr


# 테스트용 embedder, store
def fake_embed_texts(_texts):
    # shape: (1, d)에 해당하도록 리스트 한 개 반환
    return [[0.1, 0.2, 0.3]]

class FakeStoreEmpty:
    def is_empty(self):
        return True

class FakeStoreWithScore01:
    def is_empty(self):
        return False

    def search_one(self, qv, top_k=30):
        # score01이 있으면 그 값을 0~1 점수로 우선 사용
        return [
                   {"ref": "SUP-001", "score01": 0.87, "score": 0.42},
                   {"ref": "SUP-002", "score01": 0.65, "score": 0.10},
               ][:top_k]

class FakeStoreWithScoreFallback:
    def is_empty(self):
        return False

    def search_one(self, qv, top_k=30):
        # score01이 없으면 score(-1~1)를 사용하도록
        return [
                   {"ref": 123, "score": -0.2},  # ref는 숫자여도 함수에서 str로 변환됨
                   {"ref": "SUP-XYZ", "score": 0.3},
               ][:top_k]

# 테스트 코드
def test_similar_top_k_returns_empty_when_query_blank(monkeypatch):
    # 아이디어 title, description이 비어있으면 빈 리스트 반환하도록
    monkeypatch.setattr(sr, "embed_texts", lambda _: [[0.0]])

    monkeypatch.setattr(sr, "get_store", lambda: FakeStoreEmpty())

    req = StartupRequestDTO(idea_title="", idea_description="   ")
    out = sr.similar_top_k(req, k=10)
    assert out == []


def test_similar_top_k_returns_empty_when_index_empty(monkeypatch):
    # 인덱스가 비어있으면 빈 리스트 반환하도록
    monkeypatch.setattr(vectorizer, "embed_texts", fake_embed_texts)

    monkeypatch.setattr(sr, "get_store", lambda: FakeStoreEmpty())

    req = StartupRequestDTO(idea_title="AI 푸드", idea_description="이미지 인식으로 음식 분류")
    out = sr.similar_top_k(req, k=5)
    assert out == []


def test_similar_top_k_uses_score01_when_available(monkeypatch):
    # search_one 결과에 score01이 있으면 그 값을 사용
    monkeypatch.setattr(vectorizer, "embed_texts", fake_embed_texts)

    from api.embedding import index_singleton
    monkeypatch.setattr(index_singleton, "get_store", lambda: FakeStoreWithScore01())

    req = StartupRequestDTO(idea_title="스마트 주차", idea_description="V2I 기반 혼잡 예측")
    out = sr.similar_top_k(req, k=2)

    assert len(out) == 2
    assert out[0].external_ref == "SUP-001"
    # score01이 우선
    assert abs(out[0].score - 0.87) < 1e-9
    assert out[1].external_ref == "SUP-002"
    assert abs(out[1].score - 0.65) < 1e-9


def test_similar_top_k_falls_back_to_score_when_score01_missing(monkeypatch):
    # score01이 없으면 score 값을 사용
    monkeypatch.setattr(vectorizer, "embed_texts", fake_embed_texts)

    monkeypatch.setattr(sr, "get_store", lambda: FakeStoreWithScoreFallback())

    req = StartupRequestDTO(idea_title="리테일 분석", idea_description="매장 동선 트래킹")
    out = sr.similar_top_k(req, k=10)

    assert len(out) == 2
    # ref가 숫자여도 문자열로 변환되어야 함
    assert out[0].external_ref == "123"
    assert abs(out[0].score - (-0.2)) < 1e-9
    assert out[1].external_ref == "SUP-XYZ"
    assert abs(out[1].score - 0.3) < 1e-9

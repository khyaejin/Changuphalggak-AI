"""
FAISS를 이용해 벡터 인덱스를 관리하는 파일
FAISS: 벡터 검색 라이브러리 (유사도 검색에 최적화)
숫자 ID만 관리 가능하기 때문에 external_ref를 숫자 ID로 관리해주어야 함
"""

# 초기화 메서드
def __init__(self, index_path, idmap_path, dim):
    self.index_path = index_path # 인덱스를 저장할 파일 위치
    self.idmap_path = idmap_path # ref↔id 매핑 JSON 파일 위치
    self.dim = dim  # 벡터 차원
    self._index = None # 실제 FAISS 인덱스 초기화
    self._ref2id = {}  # ref(문자열) → id(int64)
    self._id2ref = {} # id(int64) → ref(문자열)
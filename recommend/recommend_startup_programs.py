import json

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import time

start_time = time.time()

# =========================
# 1. 정부 창업 지원 사업 데이터 불러오기
# =========================

with open("../data/programs.json", encoding="utf-8") as f:
    programs = json.load(f)

# =========================
# 2. 사용자 창업 idea 정의
# - 추후 REST API에서 받아올 예정
# =========================

user = {
    "age": 29,
    "has_business": False,  # 사업자 등록 여부
    "keywords": ["풋살", "영상", "스포츠", "웹서비스"],
    "description": "풋살 하이라이트 영상을 제공하는 웹서비스를 준비 중인 만 29세 예비창업자입니다."
}

# =========================
# 3. 조건 일치 점수 계산
# =========================

def condition_score(program, user):
    score = 0

    if user["age"] <= program["age_limit"]:
        score += 1
    if program["biz_required"] == user["has_business"]:
        score += 1

    keyword_match = set(user["keywords"]).intersection(set(program["keywords"]))
    score += len(keyword_match)  # 키워드 매칭 개수만큼 점수

    return score / (2 + len(program["keywords"]))

# =========================
# 4. 임베딩 모델 준비
# =========================

model = SentenceTransformer('all-MiniLM-L6-v2')

program_descs = [p["desc"] for p in programs]
program_vectors = model.encode(program_descs)
user_vector = model.encode([user["description"]])[0]

# =========================
# 5. 추천 점수 계산 및 순서 정렬
# =========================

results = []

for idx, program in enumerate(programs):
    cond_score = condition_score(program, user)
    sim_score = cosine_similarity([user_vector], [program_vectors[idx]])[0][0]
    final_score = cond_score * 0.6 + sim_score * 0.4  # 가중치는 추후 조정 예정
    results.append((program["name"], final_score, cond_score, sim_score))

results.sort(key=lambda x: x[1], reverse=True)

# =========================
# 6. 결과 출력
# =========================

print("\추천된 창업 지원사업n TOP 3\n--------------------------")
for name, final, cond, sim in results[:3]:
    print(f"[{name}]")
    print(f"  - 최종점수: {final:.3f}")
    print(f"  - 조건일치 점수: {cond:.3f}")
    print(f"  - 설명 유사도 점수: {sim:.3f}")
    print()

end_time = time.time()
duration = end_time - start_time
print(f" 실행 시간: {duration:.3f}초")
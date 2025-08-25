## [🔗](https://likelion13-changuphalgak.netlify.app) 청년의 시작, 확신으로 바꾸다. [창업할각?] - AI
<img width="900" alt="창업할각메인페이지" src="https://github.com/user-attachments/assets/20f0652d-ef72-49da-a3ab-45655cceaf18" />

> 청년 창업자를 위한 **AI 기반 맞춤형 코칭 & 지원사업 추천 플랫폼**  
> 초기 창업자의 의사결정과 지원사업 연결을 돕는 Spring Boot 기반 AI 서버

<br>

## 01 서비스 개요

* **문제 정의**

  1. 아이디어에 대한 객관적 피드백·멘토링 기회 부족
  2. 방대한 지원사업 공고·복잡한 절차로 신청 어려움
     → 창업 포기/실패 증가 → **지역 일자리·혁신 저하, 지역 격차 심화**

* **현장 인사이트**
   * 한성대·신구대 창업동아리 인터뷰:
      * “맞춤형 지원사업 추천 서비스가 필요하다”
      * “경험 부족으로 어디서부터 시작해야 할지 모르겠다”
   * 인스타그램 광고 실험: 도달 대비 클릭률 평균 이상 → **청년층의 창업 수요와 맞춤형 솔루션에 대한 높은 관심** 검증

* **솔루션**
   * <창업할각?>은 단순 정보 제공을 넘어 **AI 기반 맞춤형 플랫폼**으로서
      * 창업자의 준비 과정과 전략 수립 지원
      * 적합한 지원사업 매칭 및 사업계획서 첨삭 제공
      * 주간 실행 리포트를 통한 **지속적 코칭과 실행 지원** 제공
   * 결과적으로 **지역 창업 생태계 활성화와 균형 발전**에 기여

<br>


## 02 핵심 기능


| 분석할각?                                                                                                             | 선정될각?                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| <img width="450" alt="Image" src="https://github.com/user-attachments/assets/e0edb3d7-924e-4fe5-a640-465efb7d972f" /> | <img width="450"  alt="Image" src="https://github.com/user-attachments/assets/ca0dd534-9d7f-40e5-9ffa-da54f4b00d3b" /> |


1. **분석할각?**

- 사용자 입력(역량, 자원)을 기반으로 창업 유형/전략 분석
- AI가 SWOT/실행 로드맵 생성, 각도(Angle) 수치화해 레포트 제공
- AI 서버에서 BERT 임베딩 기반으로 수천 건 공고와 빠른 유사도 매칭
- 매주 최신 레포트 생성 후 이메일 전송

2. **선정될각?**

- 사업계획서 문항 답변에 대한 AI 첨삭
- 문항 답변, 첨삭에 기반한 예상 질의응답 제공
→ 선정 확률 향상  
 
<br/>


## 03 BERT기반 자체 AI 활용 방안
### 구현 방안
1. 문서 임베딩
- SBERT(all-MiniLM-L6-v2)로 공고 텍스트·사용자 아이디어를 384차원 벡터로 변환(L2 정규화)

2. 유사도 매칭
- FAISS로 코사인 기반 Top-K 후보 검색 → 공고 external_ref와 유사도 점수 반환

3. 추천 흐름
   * 사전 작업(앱 최초 1회 + 매일 00:00): 
   	공고 **수집·정제 → 배치 임베딩 → 인덱스 업서트**
   * 요청 시: 
   	**사용자 아이디어 임베딩 → FAISS 검색 → 상위 K 반환**


### 차별점
   1. **GPT 대비**: 토큰 한계 없이 대량 후보를 **벡터 검색**으로 즉시 비교
   2. **확장성**: 수천\~수만 건 공고로 확장 가능, 축적 데이터로 **산업군 트렌드 분석**에도 활용


## 04 기술적 완성도
### 우리가 올린 완성도 포인트
1. **정적 분석 & 리팩토링**
   * SonarQube 등으로 이슈 정리 → 심각도 순 리팩토링
2. **추천 성능 최적화**
   * FAISS **인덱스 싱글톤**(부팅 시 1회 로드), **중복 L2 정규화 제거**, **ID 벡터화 변환**, **대량 삭제 최적화(IDSelectorArray)**
   * **CPU 스레드 튜닝**을 코드로 일원화(특히 macOS OpenMP 충돌 회피), SBERT/Torch 스레드 제한
3. **운영 안정성**
   * `/health` 헬스체크, 꼼꼼한 예외처리, 자세한 로깅
4. **CI/CD**
   * 기본 파이프라인 구성(빌드·테스트·배포), 환경 변수 분리
5. **성능 개선**
   * 배포 서버 k=30 기준 **240ms → 43ms** (−82.1%, ×5.6)
   * 동일 입력 30\~100회 반복 측정, p50/p95 기록


### 참고 논문

| 참고 논문                                                                                                                            | 코드에서 참고한 부분                                                             |
| -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **1. FAISS 공식 논문** – *“FAISS: A library for efficient similarity search and clustering of dense vectors” (Johnson et al., 2017)* | 전체 인덱스 구조 설계, 내적 기반 유사도 검색 방식, `IDMap2` 활용, 벡터 추가/삭제/저장/로드 기능 구현        |
| **2. SBERT 논문** – *“Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks” (Reimers & Gurevych, 2019)*                  | 임베딩 벡터 정규화 후 내적을 코사인 유사도로 활용, 외부 참조(ref)를 `int ID`로 변환하여 검색 결과 반환 구조 적용 |




## 05 기술 스택
* **Lang/Runtime**: Python 3.11
* **Web**: FastAPI, Uvicorn(개발) / Gunicorn+UvicornWorker(운영)
* **ML**: SentenceTransformers(SBERT), FAISS
* **HTTP**: httpx(Async)
* **Data/Model**: Pydantic v2, python-dotenv
* **Infra/Obs**: 로깅, 헬스체크


## 06 아키텍처



```mermaid
flowchart TD
    %% Entry
    U[Client] -->|/startup/recommend k=30| API[FastAPI startup_router]

    %% Recommend Path
    API -->|similar_top_k| REC[recommend_service]
    REC -->|embed_texts| EMB[SBERT all MiniLM L6 v2\nModel Singleton]
    REC -->|get_store| STORE[index singleton to FaissStore]
    STORE --> IDX[FAISS index\nsupports.faiss]
    REC -->|search top k cosine| IDX
    IDX --> REC
    REC -->|SimilarSupportDTOs| API
    API -->|JSON| U

    %% Ingest and Indexing
    ADMIN[Admin or Batch Trigger] --> SYNC[fetch_startup_supports_async]
    CRON[Scheduler optional\n00:00 daily] --> SYNC
    SYNC -->|httpx| KAPI[K Startup Open API]
    SYNC --> DTO[CreateStartupResponseDTOs\ndedup and clean]
    DTO --> VEC[vectorize_and_upsert_from_dtos]
    VEC -->|embed_texts batch| EMB
    VEC -->|upsert id equals external_ref| STORE
    STORE -->|persist| IDX

    %% App Startup
    BOOT[[App startup]] --> CPU[cpu_tuning.apply_cpu_tuning\nenv limit threads]
    BOOT -->|warmup| STORE

    %% Health
    U -->|GET /health| API --> HEALTH["{status: ok}"]

    %% Styles
    classDef store fill:#eef,stroke:#5b8,stroke-width:1px;
    classDef ml fill:#eef6f


````


## 07 FastAPI 서버 실행 매뉴얼 (Ubuntu / venv 권장)


#### 0. 사전 준비 (Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version
```

#### 1. 환경 세팅

- (1) 가상환경 생성/활성화 (필수는 아니지만 권장)

```bash
cd <프로젝트_루트>   # 예: ~/AI
python3 -m venv .venv
source .venv/bin/activate

# (선택) 비활성화: deactivate
```

- (2) 패키지 설치

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
```

> 개별 설치가 필요할 때:

```bash
python -m pip install fastapi uvicorn httpx python-dotenv
```

> (옵션) PyTorch 설치가 필요하고 기본 설치가 실패하면 CPU 전용 인덱스로:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
```

- (3) 환경 변수 설정

* 프로젝트 루트에 **`.env`** 파일 생성
* 공공 데이터포털 관련 환경 변수 필요
```
SERVICE_KEY=본인이 발급받은 key
BASE_URL=http://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01
```
---

#### 2. 서버 실행

sudo apt install uvicorn
fastapi

```bash
# 가상환경 활성화된 상태에서
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* `--reload` : 코드 변경 시 자동 재시작
* `--host 0.0.0.0` : 외부 접근 허용
* `--port 8000` : 실행 포트 (기본 8000)

> 엔트리포인트가 다르면 `uvicorn api.main:app ...`, `uvicorn src.main:app ...`처럼 경로를 맞춰 주세요.

---

#### 3. 참고 자료

* FastAPI 공식 문서: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
* Uvicorn 공식 문서: [https://www.uvicorn.org/](https://www.uvicorn.org/)

---

#### 4. 트러블슈팅 빠른 체크 방안

* `externally-managed-environment`: 가상환경에서 설치했는지 확인 (`.venv` 활성화 여부)
* `pip not found`: `sudo apt install -y python3-pip` 후 `python3 -m pip ...` 사용
* `ModuleNotFoundError`: 가상환경이 맞는지, `requirements.txt` 설치가 끝났는지 확인
* 포트 점유: `lsof -i :8000` → 프로세스 종료 후 재실행

# FastAPI 서버 실행 매뉴얼

## 1. 환경 세팅

### (1) 패키지 설치

개발에 필요한 패키지는 `requirements.txt`에 정리되어 있습니다.
아래 명령어로 일괄 설치합니다.

```bash
pip install -r requirements.txt
```

추가로, 주요 패키지는 다음과 같습니다.

```bash
pip install fastapi uvicorn httpx python-dotenv
```

### (2) 환경 변수 설정

* 프로젝트 루트 경로에 `.env` 파일을 생성합니다.
* 노션에 공유된 환경 변수를 복사하여 `.env` 파일에 추가합니다.

---

## 2. 서버 실행

다음 명령어를 통해 개발 서버를 실행할 수 있습니다.

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

* `--reload` : 코드 변경 시 자동 재시작
* `--host 0.0.0.0` : 외부 접근 허용
* `--port 8000` : 실행 포트 (기본값 8000)

---

## 3. 참고 자료

* FastAPI 공식 문서: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
* Uvicorn 공식 문서: [https://www.uvicorn.org/](https://www.uvicorn.org/)


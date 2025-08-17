# FastAPI 서버 실행 매뉴얼 (Ubuntu / venv 권장)

## 0. 사전 준비 (Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
python3 --version
```

> `pip not found` 또는 `externally-managed-environment` 방지를 위해 **가상환경에서** 진행합니다.

---

## 1. 환경 세팅

### (1) 가상환경 생성/활성화 (필수는 아니지만 권장)

```bash
cd <프로젝트_루트>   # 예: ~/AI
python3 -m venv .venv
source .venv/bin/activate

# (선택) 비활성화: deactivate
```

### (2) 패키지 설치

**가상환경 활성화 상태에서** 설치하십시오.

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

> **비추천(시스템 전역 설치 강제)**
> 진짜 불가피할 때만 사용:

```bash
python -m pip install --break-system-packages -r requirements.txt
```

### (3) 환경 변수 설정

* 프로젝트 루트에 **`.env`** 파일 생성
* 노션에 공유된 환경 변수 내용을 그대로 붙여넣기

---

## 2. 서버 실행

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

## 3. 참고 자료

* FastAPI 공식 문서: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
* Uvicorn 공식 문서: [https://www.uvicorn.org/](https://www.uvicorn.org/)

---

## 4. 트러블슈팅 빠른 체크

* `externally-managed-environment`: 가상환경에서 설치했는지 확인 (`.venv` 활성화 여부)
* `pip not found`: `sudo apt install -y python3-pip` 후 `python3 -m pip ...` 사용
* `ModuleNotFoundError`: 가상환경이 맞는지, `requirements.txt` 설치가 끝났는지 확인
* 포트 점유: `lsof -i :8000` → 프로세스 종료 후 재실행

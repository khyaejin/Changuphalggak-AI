# main.py
import os 
import logging
from api.core.cpu_tuning import apply_cpu_tuning
apply_cpu_tuning(default_workers=int(os.getenv("APP_WORKERS", "1"))) # 스레드 관리

from fastapi import FastAPI
from api.routers.startup_router import router as startup_router
from api.embedding.index_singleton import get_store

# ---- 로깅 설정  ----
logger = logging.getLogger("startup_service")
logger.setLevel(logging.DEBUG)
if not logger.handlers:  # 중복 핸들러 방지
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

app = FastAPI(title="AI Server")

# 라우터 등록
app.include_router(startup_router)

# 앱 시작 시
@app.on_event("startup")
async def _warmup():
    get_store()  # 인덱스 1회 로드 (싱글톤 초기화)

# 헬스 체크
@app.get("/health")
async def health():
    return {"status": "ok"}

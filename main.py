# main.py
import logging
from fastapi import FastAPI
from api.routers.startup_router import router as startup_router

# ---- 로깅 설정  ----
logger = logging.getLogger("startup_service")
logger.setLevel(logging.DEBUG)
if not logger.handlers:  # 중복 핸들러 방지
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title="AI Server")

# 라우터 등록
app.include_router(startup_router)

# 헬스 체크
@app.get("/health")
async def health():
    return {"status": "ok"}

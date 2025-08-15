# main.py
from fastapi import FastAPI
from api.routers.startup_router import router as startup_router

app = FastAPI(title="AI Server")

# 라우터 등록
app.include_router(startup_router)

# 헬스 체크
@app.get("/health")
async def health():
    return {"status": "ok"}

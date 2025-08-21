from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# API 라우터들 import
from .api import keywords, photos, search, users
# 공모 기능은 나중에 구현 예정
# from .api import contests

app = FastAPI(
    title="LOCA Backend",
    description="대전 지역 숨은 명소 발굴을 위한 AI 기반 크라우드 소싱 플랫폼",
    version="1.0.0"
)

# CORS 설정 (React Native 앱에서 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (업로드된 이미지)
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# API 라우터 등록
app.include_router(keywords.router)
app.include_router(photos.router)
app.include_router(search.router)
app.include_router(users.router)
# 공모 기능은 나중에 구현 예정
# app.include_router(contests.router)

@app.get("/")
async def root():
    return {
        "message": "로케 Backend API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "UP",
        "service": "LOCA Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

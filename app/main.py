from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.endpoints import documents
from app.core.database import engine
# 모델들을 import하여 Base.metadata.create_all 이 모델들을 인지하게 함
import app.models.domain  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup 로직
    try:
        # 데이터베이스 및 테이블 자동 생성
        from app.core.database import init_db
        init_db()
        print("✅ 데이터베이스 스키마 및 테이블 확인/생성 완료!")

        # 데이터베이스 연결 테스트
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("✅ 데이터베이스 연결 테스트 성공!")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        
    yield
    # Shutdown 로직 (필요 시 추가)
    print("👋 애플리케이션 종료")

app = FastAPI(title="Backend API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 엔드포인트 라우터 등록
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

@app.get("/api")
def read_root():
    return {"status": "ok"}

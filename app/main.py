from fastapi import FastAPI
from app.api.endpoints import documents

app = FastAPI(title="Backend API")

# 엔드포인트 라우터 등록
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

@app.get("/api")
def read_root():
    return {"status": "ok"}

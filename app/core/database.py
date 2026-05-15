import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# 현재 파일(database.py)의 위치를 기준으로 ../../.env 경로를 찾습니다.
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=env_path)


def _build_database_url() -> str:
    """데이터베이스 URL을 생성합니다."""
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "layout_db")
    
    if not db_password:
        raise ValueError("DB_PASSWORD 환경 변수가 설정되지 않았습니다.")
    
    # 비밀번호 URL 인코딩 (특수문자 처리)
    encoded_password = quote_plus(db_password)
    
    return f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"


# 데이터베이스 URL 생성
DATABASE_URL = _build_database_url()

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 확인
    pool_recycle=3600,  # 1시간마다 연결 재생성
    pool_size=5,  # 기본 연결 풀 크기
    max_overflow=10,  # 최대 추가 연결
    echo=False  # SQL 로깅 비활성화
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()


def get_db():
    """데이터베이스 세션을 제공하는 의존성 함수"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 테이블을 초기화합니다."""
    from sqlalchemy_utils import database_exists, create_database
    
    # 데이터베이스 스키마 자체가 없으면 생성
    if not database_exists(DATABASE_URL):
        create_database(DATABASE_URL)
        print(f"✅ 데이터베이스가 자동 생성되었습니다.")
        
    Base.metadata.create_all(bind=engine)


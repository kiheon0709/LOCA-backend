from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 데이터베이스 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./loca.db"

# SQLite 엔진 생성 (동시성 개선)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={
        "check_same_thread": False,  # SQLite 전용 설정
        "timeout": 30,  # 타임아웃 설정
        "isolation_level": "IMMEDIATE"  # 즉시 잠금 모드
    },
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=300  # 5분마다 연결 재생성
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (모델들이 상속받을 클래스)
Base = declarative_base()

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

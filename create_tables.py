from app.database import engine
from app.models import Base

def create_tables():
    """데이터베이스 테이블을 생성합니다."""
    Base.metadata.create_all(bind=engine)
    print("✅ 모든 테이블이 성공적으로 생성되었습니다!")

if __name__ == "__main__":
    create_tables()

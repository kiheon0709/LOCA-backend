from app.database import engine, Base
from app.models import user, keyword, photo, like, contest, contest_photo
import os

def init_database():
    """데이터베이스 테이블을 생성합니다."""
    print("데이터베이스 테이블 생성 중...")
    
    # 모든 모델의 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    print("데이터베이스 테이블 생성 완료!")

if __name__ == "__main__":
    init_database()

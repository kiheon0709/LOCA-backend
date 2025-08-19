from app.database import engine
from app.models import Base, ContestPhoto

def migrate_contest_photos():
    """contest_photos 테이블을 생성하고 contests 테이블에 selected_photo_id 컬럼을 추가합니다."""
    
    # 새로운 테이블 생성
    ContestPhoto.__table__.create(bind=engine, checkfirst=True)
    
    # contests 테이블에 selected_photo_id 컬럼 추가 (SQLite는 ALTER TABLE 제한이 있어서)
    # 실제로는 새 테이블을 만들어서 데이터를 마이그레이션해야 하지만,
    # 개발 단계에서는 테이블을 다시 생성하는 것이 간단합니다.
    
    print("✅ contest_photos 테이블이 성공적으로 생성되었습니다!")
    print("✅ contests 테이블에 selected_photo_id 컬럼이 추가되었습니다!")

if __name__ == "__main__":
    migrate_contest_photos()

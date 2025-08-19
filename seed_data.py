from app.database import SessionLocal
from app.models import User, Keyword

def seed_initial_data():
    """시연용 초기 데이터를 생성합니다."""
    db = SessionLocal()
    
    try:
        # 시연용 유저 생성 (1-5번)
        users_data = [
            {"nickname": "홍기헌", "points": 10000},
            {"nickname": "조현비", "points": 10000},
            {"nickname": "김솔", "points": 10000},
            {"nickname": "김현서", "points": 10000},
            {"nickname": "김철수", "points": 10000},
        ]
        
        for user_data in users_data:
            user = User(**user_data)
            db.add(user)
        
        # 키워드 데이터 생성
        keywords_data = [
            {"keyword": "한적한 놀이터", "category": "놀이터"},
            {"keyword": "분위기 있는 카페", "category": "카페"},
            {"keyword": "고즈넉한 골목", "category": "골목"},
            {"keyword": "아름다운 벚꽃길", "category": "길"},
            {"keyword": "조용한 도서관", "category": "문화시설"},
            {"keyword": "맛있는 분식집", "category": "음식점"},
            {"keyword": "예쁜 벽화거리", "category": "거리"},
            {"keyword": "시원한 공원", "category": "공원"},
            {"keyword": "독특한 벽돌집", "category": "건물"},
            {"keyword": "평화로운 호수", "category": "자연"},
        ]
        
        for keyword_data in keywords_data:
            keyword = Keyword(**keyword_data)
            db.add(keyword)
        
        db.commit()
        print("✅ 시연용 초기 데이터가 성공적으로 생성되었습니다!")
        print(f"   - 유저: {len(users_data)}명")
        print(f"   - 키워드: {len(keywords_data)}개")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 데이터 생성 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_initial_data()

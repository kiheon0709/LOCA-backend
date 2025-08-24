from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import random
from datetime import datetime

from ..database import get_db
from ..models import Keyword
from ..schemas.keyword import KeywordResponse

router = APIRouter(prefix="/keywords", tags=["keywords"])

@router.get("/", response_model=List[KeywordResponse])
async def get_keywords(db: Session = Depends(get_db)):
    """모든 키워드를 조회합니다."""
    keywords = db.query(Keyword).all()
    return keywords

@router.get("/random", response_model=KeywordResponse)
async def get_random_keyword(db: Session = Depends(get_db)):
    """랜덤 키워드를 조회합니다."""
    keywords = db.query(Keyword).all()
    if not keywords:
        raise HTTPException(status_code=404, detail="키워드가 없습니다.")
    
    random_keyword = random.choice(keywords)
    return random_keyword

@router.get("/time-based", response_model=KeywordResponse)
async def get_time_based_keyword(
    time_type: str = Query(..., description="시간대: 'morning' 또는 'evening'"),
    db: Session = Depends(get_db)
):
    """시간대별 키워드를 조회합니다. 모든 사용자가 같은 키워드를 받습니다."""
    # 현재 날짜와 시간을 기반으로 결정적 키워드 선택
    now = datetime.now()
    
    # 날짜를 기준으로 결정적 키워드 선택 (모든 사용자가 같은 키워드)
    day_of_year = now.timetuple().tm_yday  # 1년 중 몇 번째 날인지
    
    # 시간대별로 다른 키워드 선택
    if time_type == "morning":
        # 아침 키워드 (7시~19시)
        keywords = db.query(Keyword).filter(Keyword.category == "morning").all()
        if not keywords:
            # 아침 카테고리가 없으면 모든 키워드에서 선택
            keywords = db.query(Keyword).all()
    else:
        # 저녁 키워드 (19시~7시)
        keywords = db.query(Keyword).filter(Keyword.category == "evening").all()
        if not keywords:
            # 저녁 카테고리가 없으면 모든 키워드에서 선택
            keywords = db.query(Keyword).all()
    
    if not keywords:
        raise HTTPException(status_code=404, detail="키워드가 없습니다.")
    
    # 날짜를 기반으로 결정적 키워드 선택
    selected_index = day_of_year % len(keywords)
    selected_keyword = keywords[selected_index]
    
    return selected_keyword

@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """특정 키워드를 조회합니다."""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    
    return keyword

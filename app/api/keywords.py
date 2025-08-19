from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import random

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

@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """특정 키워드를 조회합니다."""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    
    return keyword

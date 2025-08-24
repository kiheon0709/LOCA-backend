from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional

from ..database import get_db
from ..models import Photo, Keyword
from ..schemas.photo import PhotoResponse

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/photos", response_model=List[PhotoResponse])
async def search_photos(
    q: str = Query(..., description="검색 키워드"),
    sort_by: str = Query("latest", description="정렬 방식: latest, likes"),
    limit: int = Query(20, description="결과 개수"),
    offset: int = Query(0, description="오프셋"),
    db: Session = Depends(get_db)
):
    """AI 설명과 키워드를 기반으로 사진을 검색합니다."""
    
    # 기본 쿼리
    query = db.query(Photo)
    
    # 검색 조건: AI 설명이나 키워드에 검색어가 포함된 경우
    search_filter = or_(
        Photo.ai_description.contains(q),
        Keyword.keyword.contains(q)
    )
    
    query = query.join(Keyword).filter(search_filter)
    
    # 정렬
    if sort_by == "likes":
        # 좋아요 수로 정렬 (서브쿼리 사용)
        from ..models import Like
        like_count = db.query(func.count(Like.id)).filter(Like.photo_id == Photo.id).scalar_subquery()
        query = query.order_by(like_count.desc())
    else:  # latest
        query = query.order_by(Photo.uploaded_at.desc())
    
    # 페이징
    photos = query.offset(offset).limit(limit).all()
    
    # 각 사진의 좋아요 수 계산
    result = []
    for photo in photos:
        from ..models import Like
        like_count = db.query(Like).filter(Like.photo_id == photo.id).count()
        
        # 이미지 경로를 전체 URL로 변환
        image_url = f"http://127.0.0.1:8000/{photo.image_path}" if photo.image_path else None
        
        # photo.__dict__에서 image_path를 제거하고 새로운 image_url 사용
        photo_dict = photo.__dict__.copy()
        photo_dict.pop('image_path', None)
        
        result.append(PhotoResponse(
            **photo_dict,
            image_path=image_url,
            like_count=like_count
        ))
    
    return result

@router.get("/keywords", response_model=List[dict])
async def search_keywords(
    q: str = Query(..., description="검색 키워드"),
    db: Session = Depends(get_db)
):
    """키워드를 검색합니다."""
    keywords = db.query(Keyword).filter(
        Keyword.keyword.contains(q)
    ).all()
    
    return [{"id": k.id, "keyword": k.keyword, "category": k.category} for k in keywords]

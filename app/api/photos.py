from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from ..database import get_db
from ..models import Photo, User, Keyword, Like
from ..schemas.photo import PhotoResponse, PhotoCreate
from ..services.ai_service import ai_service

router = APIRouter(prefix="/photos", tags=["photos"])

# 업로드 디렉토리 설정
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    keyword_id: int = Form(...),
    location: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """사진을 업로드하고 AI 분석을 수행합니다."""
    
    # 유저와 키워드 존재 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    
    # 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 중 오류: {str(e)}")
    
    # 사진 데이터베이스에 저장
    photo_data = PhotoCreate(
        user_id=user_id,
        keyword_id=keyword_id,
        location=location,
        latitude=latitude,
        longitude=longitude
    )
    
    photo = Photo(
        **photo_data.dict(),
        image_path=file_path
    )
    
    db.add(photo)
    db.commit()
    db.refresh(photo)
    
    # AI 분석을 별도 세션에서 처리 (데이터베이스 잠금 방지)
    try:
        ai_description = await ai_service.analyze_image_from_path(file_path)
        if ai_description:
            # 새로운 세션으로 AI 분석 결과 업데이트
            from ..database import SessionLocal
            update_db = SessionLocal()
            try:
                update_photo = update_db.query(Photo).filter(Photo.id == photo.id).first()
                if update_photo:
                    update_photo.ai_description = ai_description
                    update_db.commit()
                    # 원래 세션의 객체도 업데이트
                    photo.ai_description = ai_description
            except Exception as update_error:
                update_db.rollback()
                print(f"AI 분석 결과 업데이트 중 오류: {update_error}")
            finally:
                update_db.close()
    except Exception as e:
        print(f"AI 분석 중 오류: {e}")
    
    # 좋아요 수 계산
    like_count = db.query(Like).filter(Like.photo_id == photo.id).count()
    
    return PhotoResponse(
        **photo.__dict__,
        like_count=like_count
    )

@router.get("/", response_model=List[PhotoResponse])
async def get_photos(
    keyword_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """사진 목록을 조회합니다."""
    query = db.query(Photo)
    
    if keyword_id:
        query = query.filter(Photo.keyword_id == keyword_id)
    
    if user_id:
        query = query.filter(Photo.user_id == user_id)
    
    photos = query.order_by(Photo.uploaded_at.desc()).offset(offset).limit(limit).all()
    
    # 각 사진의 좋아요 수 계산
    result = []
    for photo in photos:
        like_count = db.query(Like).filter(Like.photo_id == photo.id).count()
        result.append(PhotoResponse(
            **photo.__dict__,
            like_count=like_count
        ))
    
    return result

@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(photo_id: int, db: Session = Depends(get_db)):
    """특정 사진을 조회합니다."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="사진을 찾을 수 없습니다.")
    
    like_count = db.query(Like).filter(Like.photo_id == photo.id).count()
    
    return PhotoResponse(
        **photo.__dict__,
        like_count=like_count
    )

@router.post("/{photo_id}/like")
async def like_photo(photo_id: int, user_id: int, db: Session = Depends(get_db)):
    """사진에 좋아요를 추가합니다."""
    # 사진 존재 확인
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="사진을 찾을 수 없습니다.")
    
    # 이미 좋아요를 눌렀는지 확인
    existing_like = db.query(Like).filter(
        Like.photo_id == photo_id,
        Like.user_id == user_id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="이미 좋아요를 눌렀습니다.")
    
    # 좋아요 추가
    like = Like(photo_id=photo_id, user_id=user_id)
    db.add(like)
    db.commit()
    
    return {"message": "좋아요가 추가되었습니다."}

@router.delete("/{photo_id}/like")
async def unlike_photo(photo_id: int, user_id: int, db: Session = Depends(get_db)):
    """사진의 좋아요를 취소합니다."""
    like = db.query(Like).filter(
        Like.photo_id == photo_id,
        Like.user_id == user_id
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="좋아요를 찾을 수 없습니다.")
    
    db.delete(like)
    db.commit()
    
    return {"message": "좋아요가 취소되었습니다."}

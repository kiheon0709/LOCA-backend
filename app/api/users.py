from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User
from ..schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    """모든 유저 목록을 조회합니다."""
    users = db.query(User).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """특정 유저를 조회합니다."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user

@router.put("/{user_id}/points")
async def update_user_points(
    user_id: int, 
    points: int, 
    db: Session = Depends(get_db)
):
    """유저 포인트를 수정합니다."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    user.points = points
    db.commit()
    db.refresh(user)
    
    return {"message": f"유저 {user.nickname}의 포인트가 {points}로 업데이트되었습니다.", "user": user}

@router.get("/{user_id}/stats")
async def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """유저 통계를 조회합니다."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    # 업로드한 사진 수
    photo_count = db.query(user.photos).count()
    
    # 받은 좋아요 수
    received_likes = db.query(user.photos).join(user.likes).count()
    
    # 생성한 공모 수
    contest_count = db.query(user.contests).count()
    
    # 참여한 공모 수
    participated_contests = db.query(user.contest_photos).distinct().count()
    
    return {
        "user_id": user_id,
        "nickname": user.nickname,
        "points": user.points,
        "photo_count": photo_count,
        "received_likes": received_likes,
        "contest_count": contest_count,
        "participated_contests": participated_contests
    }

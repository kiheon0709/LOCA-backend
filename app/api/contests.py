from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from ..database import get_db
from ..models import Contest, ContestPhoto, User, ContestStatus
from ..schemas.contest import ContestCreate, ContestResponse, ContestUpdate
from ..schemas.contest_photo import ContestPhotoCreate, ContestPhotoResponse

router = APIRouter(prefix="/contests", tags=["contests"])

# 업로드 디렉토리 설정
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=ContestResponse)
async def create_contest(
    contest_data: ContestCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """공모를 생성합니다."""
    
    # 유저 존재 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    # 포인트 확인
    if user.points < contest_data.points:
        raise HTTPException(status_code=400, detail="포인트가 부족합니다.")
    
    # 공모 생성
    contest = Contest(
        **contest_data.dict(),
        user_id=user_id
    )
    
    # 포인트 차감
    user.points -= contest_data.points
    
    db.add(contest)
    db.commit()
    db.refresh(contest)
    
    return ContestResponse(
        **contest.__dict__,
        photo_count=0
    )

@router.get("/", response_model=List[ContestResponse])
async def get_contests(
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """공모 목록을 조회합니다."""
    query = db.query(Contest)
    
    if status:
        query = query.filter(Contest.status == ContestStatus(status))
    
    if user_id:
        query = query.filter(Contest.user_id == user_id)
    
    contests = query.order_by(Contest.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for contest in contests:
        photo_count = db.query(ContestPhoto).filter(ContestPhoto.contest_id == contest.id).count()
        result.append(ContestResponse(
            **contest.__dict__,
            photo_count=photo_count
        ))
    
    return result

@router.get("/{contest_id}", response_model=ContestResponse)
async def get_contest(contest_id: int, db: Session = Depends(get_db)):
    """특정 공모를 조회합니다."""
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="공모를 찾을 수 없습니다.")
    
    photo_count = db.query(ContestPhoto).filter(ContestPhoto.contest_id == contest.id).count()
    
    return ContestResponse(
        **contest.__dict__,
        photo_count=photo_count
    )

@router.post("/{contest_id}/photos", response_model=ContestPhotoResponse)
async def submit_contest_photo(
    contest_id: int,
    file: UploadFile = File(...),
    user_id: int = Form(...),
    location: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """공모에 사진을 제출합니다."""
    
    # 공모 존재 확인
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="공모를 찾을 수 없습니다.")
    
    # 공모 상태 확인
    if contest.status != ContestStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="마감된 공모입니다.")
    
    # 유저 존재 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    # 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contest_{contest_id}_{user_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 저장 중 오류: {str(e)}")
    
    # 공모 사진 데이터베이스에 저장
    contest_photo_data = ContestPhotoCreate(
        contest_id=contest_id,
        location=location,
        latitude=latitude,
        longitude=longitude,
        description=description
    )
    
    contest_photo = ContestPhoto(
        **contest_photo_data.dict(),
        user_id=user_id,
        image_path=file_path
    )
    
    db.add(contest_photo)
    db.commit()
    db.refresh(contest_photo)
    
    return ContestPhotoResponse(
        **contest_photo.__dict__,
        user_nickname=user.nickname
    )

@router.get("/{contest_id}/photos", response_model=List[ContestPhotoResponse])
async def get_contest_photos(
    contest_id: int,
    db: Session = Depends(get_db)
):
    """공모에 제출된 사진들을 조회합니다."""
    
    # 공모 존재 확인
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="공모를 찾을 수 없습니다.")
    
    contest_photos = db.query(ContestPhoto).filter(
        ContestPhoto.contest_id == contest_id
    ).order_by(ContestPhoto.submitted_at.desc()).all()
    
    result = []
    for photo in contest_photos:
        user = db.query(User).filter(User.id == photo.user_id).first()
        result.append(ContestPhotoResponse(
            **photo.__dict__,
            user_nickname=user.nickname if user else ""
        ))
    
    return result

@router.put("/{contest_id}/select")
async def select_contest_photo(
    contest_id: int,
    photo_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """공모에서 사진을 선택합니다."""
    
    # 공모 존재 확인
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="공모를 찾을 수 없습니다.")
    
    # 공모 주최자 확인
    if contest.user_id != user_id:
        raise HTTPException(status_code=403, detail="공모 주최자만 선택할 수 있습니다.")
    
    # 사진 존재 확인
    contest_photo = db.query(ContestPhoto).filter(
        ContestPhoto.id == photo_id,
        ContestPhoto.contest_id == contest_id
    ).first()
    if not contest_photo:
        raise HTTPException(status_code=404, detail="사진을 찾을 수 없습니다.")
    
    # 공모 상태 업데이트
    contest.selected_photo_id = photo_id
    contest.status = ContestStatus.COMPLETED
    contest.completed_at = datetime.now()
    
    # 포인트 지급
    winner = db.query(User).filter(User.id == contest_photo.user_id).first()
    if winner:
        winner.points += contest.points
    
    db.commit()
    
    return {"message": "사진이 선택되었고 포인트가 지급되었습니다."}

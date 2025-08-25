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
CONTESTS_DIR = os.path.join(UPLOAD_DIR, "contests")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CONTESTS_DIR, exist_ok=True)

def get_contest_upload_dir(contest_id: int) -> str:
    """공모별 업로드 디렉토리를 생성하고 반환합니다."""
    contest_dir = os.path.join(CONTESTS_DIR, str(contest_id))
    os.makedirs(contest_dir, exist_ok=True)
    return contest_dir

def migrate_existing_contest_photos(db: Session):
    """기존에 uploads/ 디렉토리에 저장된 공모 사진들을 공모별로 분류합니다."""
    try:
        # 기존 uploads 디렉토리의 모든 파일 확인
        if not os.path.exists(UPLOAD_DIR):
            return
        
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith('contest_') and filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                # 데이터베이스에서 해당 파일 경로를 가진 공모 사진 찾기
                contest_photo = db.query(ContestPhoto).filter(ContestPhoto.image_path == file_path).first()
                if contest_photo:
                    # 공모별 디렉토리로 이동
                    contest_dir = get_contest_upload_dir(contest_photo.contest_id)
                    new_file_path = os.path.join(contest_dir, filename)
                    
                    # 파일 이동
                    if os.path.exists(file_path) and not os.path.exists(new_file_path):
                        shutil.move(file_path, new_file_path)
                        
                        # 데이터베이스 경로 업데이트
                        contest_photo.image_path = new_file_path
                        db.commit()
                        print(f"공모 사진 마이그레이션 완료: {filename} -> {new_file_path}")
                        
    except Exception as e:
        print(f"공모 사진 마이그레이션 중 오류: {e}")
        db.rollback()

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
    
    # 공모 생성
    contest_data_dict = contest_data.dict()
    
    # deadline이 문자열로 전달된 경우 datetime으로 변환
    if contest_data_dict.get('deadline') and isinstance(contest_data_dict['deadline'], str):
        try:
            contest_data_dict['deadline'] = datetime.fromisoformat(contest_data_dict['deadline'].replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다.")
    
    contest = Contest(
        **contest_data_dict,
        user_id=user_id
    )
    
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

@router.get("/applied", response_model=List[ContestResponse])
async def get_applied_contests(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """특정 유저가 사진을 제출하여 지원한 공모 목록을 조회합니다."""
    # 유저 존재 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    # 해당 유저가 제출한 사진들의 공모 ID 목록 (중복 제거)
    subquery = db.query(ContestPhoto.contest_id).filter(ContestPhoto.user_id == user_id).distinct().subquery()

    contests = db.query(Contest).filter(Contest.id.in_(subquery)).order_by(Contest.created_at.desc()).offset(offset).limit(limit).all()

    result: List[ContestResponse] = []
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
    contest_upload_dir = get_contest_upload_dir(contest_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{user_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(contest_upload_dir, filename)
    
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
    
    # 공모 주최자 포인트 확인
    contest_owner = db.query(User).filter(User.id == user_id).first()
    if not contest_owner:
        raise HTTPException(status_code=404, detail="공모 주최자를 찾을 수 없습니다.")
    
    if contest_owner.points < contest.points:
        raise HTTPException(status_code=400, detail="포인트가 부족합니다.")
    
    # 공모 상태 업데이트
    contest.selected_photo_id = photo_id
    contest.status = ContestStatus.COMPLETED
    contest.completed_at = datetime.now()
    
    # 포인트 차감 및 지급
    contest_owner.points -= contest.points  # 공모 주최자 포인트 차감
    winner = db.query(User).filter(User.id == contest_photo.user_id).first()
    if winner:
        winner.points += contest.points  # 우승자 포인트 지급
    
    db.commit()
    
    return {"message": "사진이 선택되었고 포인트가 지급되었습니다."}

@router.delete("/{contest_id}")
async def delete_contest(
    contest_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """공모를 삭제합니다. (마감된 공모만 삭제 가능)"""
    
    # 공모 존재 확인
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="공모를 찾을 수 없습니다.")
    
    # 공모 주최자 확인
    if contest.user_id != user_id:
        raise HTTPException(status_code=403, detail="공모 주최자만 삭제할 수 있습니다.")
    
    # 마감된 공모만 삭제 가능
    if contest.status != ContestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="마감된 공모만 삭제할 수 있습니다.")
    
    # 공모에 제출된 사진들 삭제
    contest_photos = db.query(ContestPhoto).filter(ContestPhoto.contest_id == contest_id).all()
    for photo in contest_photos:
        # 파일 삭제
        if os.path.exists(photo.image_path):
            os.remove(photo.image_path)
        # 데이터베이스에서 삭제
        db.delete(photo)
    
    # 공모 디렉토리 삭제
    contest_dir = get_contest_upload_dir(contest_id)
    if os.path.exists(contest_dir):
        shutil.rmtree(contest_dir)
    
    # 공모 삭제
    db.delete(contest)
    db.commit()
    
    return {"message": "공모가 성공적으로 삭제되었습니다."}

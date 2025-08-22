from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
import json
import aiofiles
import aiohttp

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
    
    print(f"업로드 요청 받음: user_id={user_id}, keyword_id={keyword_id}")
    print(f"파일 정보: filename={file.filename}, content_type={file.content_type}")
    print(f"위치 정보: location={location}, lat={latitude}, lng={longitude}")
    
    # 유저와 키워드 존재 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"유저를 찾을 수 없음: user_id={user_id}")
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        print(f"키워드를 찾을 수 없음: keyword_id={keyword_id}")
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    
    print(f"유저와 키워드 확인 완료: user={user.nickname}, keyword={keyword.keyword}")
    
    # 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        # 파일 내용을 먼저 읽어서 저장
        file_content = await file.read()
        print(f"파일 내용 읽기 완료: {len(file_content)} bytes")
        
        # 파일 내용이 비어있는지 확인
        if len(file_content) == 0:
            print("오류: 파일 내용이 비어있습니다!")
            raise HTTPException(status_code=400, detail="빈 파일입니다.")
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 파일 저장 확인
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"파일 저장 완료: {file_path}, 크기: {file_size} bytes")
            
            if file_size == 0:
                print("경고: 저장된 파일이 비어있습니다!")
                raise HTTPException(status_code=500, detail="파일 저장에 실패했습니다.")
            elif file_size != len(file_content):
                print(f"경고: 저장된 파일 크기가 다릅니다! 읽은 크기: {len(file_content)}, 저장된 크기: {file_size}")
        else:
            print(f"오류: 파일이 저장되지 않았습니다: {file_path}")
            raise HTTPException(status_code=500, detail="파일 저장에 실패했습니다.")
            
    except Exception as e:
        print(f"파일 저장 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 저장 중 오류: {str(e)}")
    
    # 사진 데이터베이스에 저장 (데이터베이스 잠금 방지)
    try:
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
        print(f"데이터베이스 저장 완료: photo_id={photo.id}")
        
    except Exception as db_error:
        db.rollback()
        print(f"데이터베이스 저장 중 오류: {db_error}")
        # 파일도 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"데이터베이스 저장 중 오류: {str(db_error)}")
    
    # AI 분석 - 파일 경로 사용 (ai-test.py와 동일한 방식)
    try:
        print(f"AI 분석 시작: {file_path}")
        
        # 파일 존재 및 크기 확인
        if not os.path.exists(file_path):
            print(f"AI 분석 실패: 파일이 존재하지 않음 - {file_path}")
            ai_description = "파일을 찾을 수 없어 분석할 수 없습니다."
        else:
            file_size = os.path.getsize(file_path)
            print(f"AI 분석 대상 파일 크기: {file_size} bytes")
            
            if file_size == 0:
                print("AI 분석 실패: 파일이 비어있음")
                ai_description = "빈 파일로 분석할 수 없습니다."
            else:
                # ai-test.py와 동일한 방식: 파일 경로로 AI 분석
                ai_description = await ai_service.analyze_image_from_path(file_path)
                print(f"AI 분석 결과: {ai_description}")
        
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
                    print(f"AI 분석 결과 데이터베이스 업데이트 완료")
            except Exception as update_error:
                update_db.rollback()
                print(f"AI 분석 결과 업데이트 중 오류: {update_error}")
            finally:
                update_db.close()
    except Exception as e:
        print(f"AI 분석 중 오류: {e}")
        import traceback
        print(f"AI 분석 오류 스택 트레이스: {traceback.format_exc()}")
    
    # 좋아요 수 계산
    like_count = db.query(Like).filter(Like.photo_id == photo.id).count()
    
    return PhotoResponse(
        **photo.__dict__,
        like_count=like_count
    )

@router.post("/upload-asset", response_model=PhotoResponse)
async def upload_photo_from_asset(
    request: Request,
    user_id: int = Form(...),
    keyword_id: int = Form(...),
    location: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    """asset 객체를 받아서 사진을 업로드하고 AI 분석을 수행합니다."""
    
    print(f"asset 업로드 요청 받음: user_id={user_id}, keyword_id={keyword_id}")
    print(f"위치 정보: location={location}, lat={latitude}, lng={longitude}")
    
    # 유저와 키워드 존재 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"유저를 찾을 수 없음: user_id={user_id}")
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        print(f"키워드를 찾을 수 없음: keyword_id={keyword_id}")
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    
    print(f"유저와 키워드 확인 완료: user={user.nickname}, keyword={keyword.keyword}")
    
    try:
        # FormData에서 asset 정보 추출
        form_data = await request.form()
        asset_data = form_data.get("asset")
        
        if not asset_data:
            print("asset 데이터가 없습니다!")
            raise HTTPException(status_code=400, detail="asset 데이터가 없습니다.")
        
        # asset 데이터 파싱 (JSON 문자열로 전송되었다고 가정)
        try:
            asset_info = json.loads(asset_data) if isinstance(asset_data, str) else asset_data
            print(f"asset 정보: {asset_info}")
        except json.JSONDecodeError:
            print(f"asset 데이터 파싱 실패: {asset_data}")
            raise HTTPException(status_code=400, detail="잘못된 asset 데이터 형식입니다.")
        
        # asset에서 파일 URI 추출
        file_uri = asset_info.get("uri")
        if not file_uri:
            print("asset에서 uri를 찾을 수 없습니다!")
            raise HTTPException(status_code=400, detail="asset에서 파일 URI를 찾을 수 없습니다.")
        
        print(f"파일 URI: {file_uri}")
        
        # 파일 다운로드 또는 로컬 파일 읽기
        if file_uri.startswith('file://'):
            # 로컬 파일인 경우 직접 읽기
            local_path = file_uri.replace('file://', '')
            print(f"로컬 파일 경로: {local_path}")
            
            try:
                async with aiofiles.open(local_path, 'rb') as f:
                    file_content = await f.read()
                print(f"로컬 파일 읽기 완료: {len(file_content)} bytes")
            except Exception as e:
                print(f"로컬 파일 읽기 실패: {e}")
                raise HTTPException(status_code=400, detail=f"로컬 파일을 읽을 수 없습니다: {str(e)}")
        else:
            # HTTP URL인 경우 다운로드
            async with aiohttp.ClientSession() as session:
                async with session.get(file_uri) as response:
                    if response.status != 200:
                        print(f"파일 다운로드 실패: {response.status}")
                        raise HTTPException(status_code=400, detail="파일을 다운로드할 수 없습니다.")
                    
                    file_content = await response.read()
                    print(f"파일 다운로드 완료: {len(file_content)} bytes")
        
        # 파일 내용이 비어있는지 확인
        if len(file_content) == 0:
            print("오류: 파일 내용이 비어있습니다!")
            raise HTTPException(status_code=400, detail="빈 파일입니다.")
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{timestamp}_asset_image.jpg"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(file_content)
        
        # 파일 저장 확인
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"파일 저장 완료: {file_path}, 크기: {file_size} bytes")
            
            if file_size == 0:
                print("경고: 저장된 파일이 비어있습니다!")
                raise HTTPException(status_code=500, detail="파일 저장에 실패했습니다.")
            elif file_size != len(file_content):
                print(f"경고: 저장된 파일 크기가 다릅니다! 읽은 크기: {len(file_content)}, 저장된 크기: {file_size}")
        else:
            print(f"오류: 파일이 저장되지 않았습니다: {file_path}")
            raise HTTPException(status_code=500, detail="파일 저장에 실패했습니다.")
            
    except Exception as e:
        print(f"파일 처리 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류: {str(e)}")
    
    # 사진 데이터베이스에 저장 (데이터베이스 잠금 방지)
    try:
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
        print(f"데이터베이스 저장 완료: photo_id={photo.id}")
        
    except Exception as db_error:
        db.rollback()
        print(f"데이터베이스 저장 중 오류: {db_error}")
        # 파일도 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"데이터베이스 저장 중 오류: {str(db_error)}")
    
    # AI 분석 - 파일 경로 사용 (ai-test.py와 동일한 방식)
    try:
        print(f"AI 분석 시작: {file_path}")
        
        # 파일 존재 및 크기 확인
        if not os.path.exists(file_path):
            print(f"AI 분석 실패: 파일이 존재하지 않음 - {file_path}")
            ai_description = "파일을 찾을 수 없어 분석할 수 없습니다."
        else:
            file_size = os.path.getsize(file_path)
            print(f"AI 분석 대상 파일 크기: {file_size} bytes")
            
            if file_size == 0:
                print("AI 분석 실패: 파일이 비어있음")
                ai_description = "빈 파일로 분석할 수 없습니다."
            else:
                # ai-test.py와 동일한 방식: 파일 경로로 AI 분석
                ai_description = await ai_service.analyze_image_from_path(file_path)
                print(f"AI 분석 결과: {ai_description}")
        
        if ai_description:
            # AI 분석 결과를 데이터베이스에 업데이트
            photo.ai_description = ai_description
            db.commit()
            print(f"AI 분석 결과 저장 완료: {ai_description[:50]}...")
        
    except Exception as e:
        print(f"AI 분석 중 오류: {e}")
        import traceback
        print(f"AI 분석 오류 스택 트레이스: {traceback.format_exc()}")
    
    return PhotoResponse.from_orm(photo)

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

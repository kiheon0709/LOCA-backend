from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ContestPhotoBase(BaseModel):
    contest_id: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class ContestPhotoCreate(ContestPhotoBase):
    pass

class ContestPhotoUpdate(BaseModel):
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class ContestPhoto(ContestPhotoBase):
    id: int
    user_id: int
    image_path: str
    submitted_at: datetime
    
    class Config:
        from_attributes = True

class ContestPhotoResponse(BaseModel):
    id: int
    contest_id: int
    user_id: int
    image_path: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    submitted_at: datetime
    user_nickname: str = ""  # 유저 닉네임

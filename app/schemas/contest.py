from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ContestStatusEnum(str, Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

class ContestBase(BaseModel):
    title: str
    description: str
    points: int

class ContestCreate(ContestBase):
    pass

class ContestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    points: Optional[int] = None
    status: Optional[ContestStatusEnum] = None
    selected_photo_id: Optional[int] = None

class Contest(ContestBase):
    id: int
    user_id: int
    status: ContestStatusEnum
    selected_photo_id: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ContestResponse(BaseModel):
    id: int
    title: str
    description: str
    points: int
    status: ContestStatusEnum
    user_id: int
    selected_photo_id: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    photo_count: int = 0  # 참여 사진 수

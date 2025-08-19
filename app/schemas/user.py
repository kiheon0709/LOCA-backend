from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    nickname: str

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    points: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    nickname: str
    points: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    points: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    nickname: str
    points: int

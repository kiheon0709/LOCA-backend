from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PhotoBase(BaseModel):
    user_id: int
    keyword_id: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class PhotoCreate(PhotoBase):
    pass

class PhotoUpdate(BaseModel):
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ai_description: Optional[str] = None

class Photo(PhotoBase):
    id: int
    image_path: str
    ai_description: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class PhotoResponse(BaseModel):
    id: int
    user_id: int
    keyword_id: int
    image_path: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ai_description: Optional[str] = None
    uploaded_at: datetime
    like_count: int = 0

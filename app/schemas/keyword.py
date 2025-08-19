from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class KeywordBase(BaseModel):
    keyword: str
    category: Optional[str] = None

class KeywordCreate(KeywordBase):
    pass

class Keyword(KeywordBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class KeywordResponse(BaseModel):
    id: int
    keyword: str
    category: Optional[str] = None

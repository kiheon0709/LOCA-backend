from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=True)  # 예: "놀이터", "카페", "골목" 등
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    photos = relationship("Photo", back_populates="keyword")
    
    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', category='{self.category}')>"

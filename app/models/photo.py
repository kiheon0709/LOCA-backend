from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False)
    image_path = Column(String(500), nullable=False)  # 이미지 파일 경로
    location = Column(String(200), nullable=True)  # 위치 정보
    latitude = Column(Float, nullable=True)  # 위도
    longitude = Column(Float, nullable=True)  # 경도
    ai_description = Column(Text, nullable=True)  # AI 분석 결과
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="photos")
    keyword = relationship("Keyword", back_populates="photos")
    likes = relationship("Like", back_populates="photo")
    
    def __repr__(self):
        return f"<Photo(id={self.id}, user_id={self.user_id}, keyword_id={self.keyword_id})>"

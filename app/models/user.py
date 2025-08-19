from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(50), unique=True, index=True, nullable=False)
    points = Column(Integer, default=10000)  # 시연용 초기 포인트
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    photos = relationship("Photo", back_populates="user")
    likes = relationship("Like", back_populates="user")
    contests = relationship("Contest", back_populates="user")
    contest_photos = relationship("ContestPhoto", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, nickname='{self.nickname}', points={self.points})>"

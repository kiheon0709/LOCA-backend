from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Like(Base):
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="likes")
    photo = relationship("Photo", back_populates="likes")
    
    # 한 사용자가 한 사진에 좋아요를 한 번만 할 수 있도록 제약
    __table_args__ = (UniqueConstraint('user_id', 'photo_id', name='unique_user_photo_like'),)
    
    def __repr__(self):
        return f"<Like(id={self.id}, user_id={self.user_id}, photo_id={self.photo_id})>"

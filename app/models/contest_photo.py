from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class ContestPhoto(Base):
    __tablename__ = "contest_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String(500), nullable=False)
    location = Column(String(200), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)  # 참여자가 작성한 설명
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    contest = relationship("Contest", back_populates="contest_photos", foreign_keys=[contest_id])
    user = relationship("User")
    
    def __repr__(self):
        return f"<ContestPhoto(id={self.id}, contest_id={self.contest_id}, user_id={self.user_id})>"

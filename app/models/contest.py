from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base

class ContestStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Contest(Base):
    __tablename__ = "contests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    points = Column(Integer, nullable=False)  # 공모에 걸린 포인트
    status = Column(Enum(ContestStatus), default=ContestStatus.ACTIVE)
    selected_photo_id = Column(Integer, ForeignKey("contest_photos.id"), nullable=True)  # 선택된 사진
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 관계 설정
    user = relationship("User", back_populates="contests")
    contest_photos = relationship("ContestPhoto", back_populates="contest", foreign_keys="[ContestPhoto.contest_id]")
    selected_photo = relationship("ContestPhoto", foreign_keys=[selected_photo_id], post_update=True)
    
    def __repr__(self):
        return f"<Contest(id={self.id}, title='{self.title}', points={self.points}, status={self.status.value})>"

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class UserSaved(Base):
    __tablename__ = "user_saved"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content_id = Column(Integer, ForeignKey("contents.content_id"), nullable=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    created_at = Column(DateTime)
    
    content = relationship("Content", back_populates="user_saved")
    episode = relationship("Episode", back_populates="user_saved")
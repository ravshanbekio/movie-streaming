from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class UserHistory(Base):
    __tablename__ = "user_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    content_id = Column(Integer, ForeignKey("contents.content_id", ondelete="CASCADE"))
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True)
    duration = Column(String(255))
    created_at = Column(DateTime)

    content = relationship("Content", back_populates="user_history")
    episode = relationship("Episode", back_populates="user_history")
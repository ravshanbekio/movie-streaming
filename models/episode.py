from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, foreign

from database import Base

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("contents.content_id"))
    seasion = Column(Integer)
    episode = Column(Integer)
    episode_video = Column(String(255))
    episode_thumbnail = Column(String(255))
    duration = Column(String(255))
    is_processing = Column(Boolean, default=False)
    created_at = Column(DateTime)

    # Relationships
    content = relationship("Content", primaryjoin="Episode.content_id==Content.content_id", back_populates="episodes")
    user_history = relationship("UserHistory", back_populates="episode")
    user_saved = relationship("UserSaved", back_populates="episode")
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database import Base

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("contents.content_id"))
    seasion = Column(String(25))
    episode = Column(String(50))
    episode_video = Column(String(255))
    episode_thumbnail = Column(String(255))
    duration = Column(Integer, default=0)
    is_processing = Column(Boolean, default=True)
    created_at = Column(DateTime)

    # Relationships
    content = relationship("Content", primaryjoin="Content.content_id==Episode.content_id", back_populates="episodes")
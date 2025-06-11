from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship

from database import Base
from models.content import Content

class Playlist(Base):
    __tablename__ = "playlists"

    playlist_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    thumbnail = Column(String(255))
    created_at = Column(DateTime)

    # Relationships
    contents = relationship("Content", back_populates="playlist")
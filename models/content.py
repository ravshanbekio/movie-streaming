from sqlalchemy import Column, String, Integer, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base

class Playlist(Base):
    __tablename__ = "playlists"

    playlist_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    thumbnail = Column(String(255))
    created_at = Column(DateTime)

    # Relationships
    contents = relationship("Content", back_populates="playlist")

class Content(Base):
    __tablename__ = "contents"

    content_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    genre = Column(Integer, ForeignKey("genres.genre_id"))
    quality = Column(String(10), nullable=True)
    release_date = Column(Date, nullable=True)
    dubbed_by = Column(String(255), nullable=True)
    thumbnail = Column(String(255))
    content_url = Column(String(255))
    playlist_id = Column(Integer, ForeignKey("playlists.playlist_id"), nullable=True)
    created_at = Column(DateTime)

    # Relationships
    genre_data = relationship("Genre", primaryjoin="Content.genre==Genre.genre_id", back_populates="content")
    playlist = relationship("Playlist", primaryjoin="Content.playlist_id==Playlist.playlist_id", back_populates="contents")
from sqlalchemy import Column, String, Integer, Date, DateTime, Text, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship

from database import Base
from .episode import Episode
from .genre import Genre
from .user_history import UserHistory
from .user_saved import UserSaved
from .association import movie_genre_association


class Content(Base):
    __tablename__ = "contents"

    content_id = Column(Integer, primary_key=True, autoincrement=True)
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255))
    description = Column(Text, nullable=True)
    quality = Column(String(10), nullable=True)
    release_date = Column(Date, nullable=True)
    dubbed_by = Column(String(255), nullable=True)
    status = Column(String(100))
    subscription_status = Column(Boolean, default=False)
    thumbnail = Column(String(255))
    original_content = Column(String(255))
    converted_content = Column(String(255), nullable=True)
    original_trailer = Column(String(255), nullable=True)
    converted_trailer = Column(String(255), nullable=True)
    content_duration = Column(String(255), nullable=True)
    trailer_duration = Column(String(255), nullable=True)
    is_processing = Column(Boolean, default=False)
    type = Column(String(100))
    created_at = Column(DateTime)

    # Relationships
    genre_data = relationship("Genre", secondary=movie_genre_association, back_populates="content")
    episodes = relationship("Episode", back_populates="content")
    user_history = relationship("UserHistory", back_populates="content")
    user_saved = relationship("UserSaved", back_populates="content")
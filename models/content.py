from sqlalchemy import Column, String, Integer, Date, DateTime, Text, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship

from database import Base
from .episode import Episode

# movie_genre_association = Table(
#     'movie_genre',
#     Base.metadata,
#     Column('content_id', ForeignKey('contents.content_id'), primary_key=True),
#     Column('genre_id', ForeignKey('genres.genre_id'), primary_key=True)
# )

class Content(Base):
    __tablename__ = "contents"

    content_id = Column(Integer, primary_key=True, autoincrement=True)
    uploader_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    description = Column(Text, nullable=True)
    genre = Column(Integer, ForeignKey("genres.genre_id"), nullable=True)
    quality = Column(String(10), nullable=True)
    release_date = Column(Date, nullable=True)
    dubbed_by = Column(String(255), nullable=True)
    status = Column(String(100))
    subscription_status = Column(Boolean, default=False)
    thumbnail = Column(String(255))
    content_url = Column(String(255))
    trailer_url = Column(String(255), nullable=True)
    is_processing = Column(Boolean, default=True)
    created_at = Column(DateTime)

    # Relationships
    #genre_data = relationship("Genre", secondary=movie_genre_association, back_populates="content")
    episodes = relationship("Episode", back_populates="content")
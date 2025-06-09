from sqlalchemy import Column, Integer, String, DateTime

from database import Base

class Genre(Base):
    __tablename__ = "genres"

    genre_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    created_at = Column(DateTime)
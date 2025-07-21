from sqlalchemy import Column, String, Integer, Date, DateTime, Text, ForeignKey, Boolean, Table
from database import Base


movie_genre_association = Table(
    'movie_genre',
    Base.metadata,
    Column('content_id', ForeignKey('contents.content_id'), primary_key=True),
    Column('genre_id', ForeignKey('genres.genre_id'), primary_key=True)
)
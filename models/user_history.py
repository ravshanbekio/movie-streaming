from sqlalchemy import Column, Integer, DateTime, ForeignKey

from database import Base

class UserHistory(Base):
    __tablename__ = "user_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content_id = Column(Integer, ForeignKey("contents.content_id"))
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True)
    created_at = Column(DateTime)

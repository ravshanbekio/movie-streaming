from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from database import Base

class UserToken(Base):
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    access_token = Column(String(255), unique=True)
    refresh_token = Column(String(255), unique=True)
    user_device = Column(String(100), nullable=True)
    created_at = Column(DateTime)
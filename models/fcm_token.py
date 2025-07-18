from sqlalchemy import Column, String, Integer, DateTime, ForeignKey

from database import Base

class FCMToken(Base):
    __tablename__ = "fcm_token"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(255))
    create_at = Column(DateTime)
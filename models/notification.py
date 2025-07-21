from sqlalchemy import Column, Integer, String, Text, DateTime

from database import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    body = Column(Text, nullable=True)
    created_at = Column(DateTime)
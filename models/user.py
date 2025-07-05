from sqlalchemy import Column, Integer, String, Boolean, DateTime

from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone_number = Column(String(13))
    password = Column(String(255))
    subscribed = Column(Boolean, default=False)
    status = Column(String(8), default="active")
    role = Column(String(30))
    joined_at = Column(DateTime)
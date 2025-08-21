from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from database import Base
from .user_token import UserToken

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone_number = Column(String(13))
    password = Column(String(255))
    country = Column(String(10), nullable=True)
    subscribed = Column(Boolean, default=False)
    status = Column(String(8), default="active")
    role = Column(String(30))
    code = Column(BigInteger, default=0, nullable=True)
    joined_at = Column(DateTime)
    
    user_token = relationship("UserToken", back_populates="user_data")
    order = relationship("Order", uselist=False, back_populates="user")
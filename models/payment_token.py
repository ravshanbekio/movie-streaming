from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey

from database import Base

class PaymentToken(Base):
    __tablename__ = "payment_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(255))
    active = Column(Boolean, default=True)
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func

from database import Base

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    gateway = Column(String(100))
    account_id = Column(String(255))
    transaction_id = Column(String(255))
    amount = Column(BigInteger, nullable=True)
    extra_data = Column(String(400))
    state = Column(Integer)
    reason = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())
    performed_at = Column(DateTime, server_default=func.now())
    cancelled_at = Column(DateTime, server_default=func.now())
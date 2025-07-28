from sqlalchemy import Column, Integer ,BigInteger, String, DateTime, CheckConstraint

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
    reason = Column(Integer, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    performed_at = Column(DateTime, default=0)
    cancelled_at = Column(DateTime, default=0)
    
    __table_args__ = (
        CheckConstraint('state > 0', name='check_state'),
    )
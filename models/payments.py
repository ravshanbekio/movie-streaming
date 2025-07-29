from sqlalchemy import Column, Integer ,BigInteger, String, DateTime, CheckConstraint, event
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
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
    performed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    # Milliseconds
    created_at_ms = Column(BigInteger)
    updated_at_ms = Column(BigInteger)
    performed_at_ms = Column(BigInteger)
    cancelled_at_ms = Column(BigInteger)
    
    __table_args__ = (
        CheckConstraint('state IN (-2, -1, 1, 2)', name='check_valid_states'),
    )
    
    
def datetime_to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000) if dt else None

@event.listens_for(Payment, "before_insert")
@event.listens_for(Payment, "before_update")
def populate_unix_ms_fields(mapper, connection, target: Payment):
    target.created_at_ms = datetime_to_ms(target.created_at)
    target.updated_at_ms = datetime_to_ms(target.updated_at)
    target.performed_at_ms = datetime_to_ms(target.performed_at)
    target.cancelled_at_ms = datetime_to_ms(target.cancelled_at)
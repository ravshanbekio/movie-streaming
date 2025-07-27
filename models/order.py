from sqlalchemy import Column, BigInteger, Integer, String, Date, DateTime, ForeignKey

from database import Base

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    promocode_id = Column(Integer, ForeignKey("promocodes.id"), nullable=True)
    amount = Column(BigInteger)
    created_at = Column(DateTime)
    next_payment_date = Column(Date)
    status = Column(String(255), default="free")
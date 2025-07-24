from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey

from database import Base

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    promocode_id = Column(Integer, ForeignKey("promocodes.id"), nullable=True)
    total_price = Column(BigInteger)
    created_at = Column(DateTime)
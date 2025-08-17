from sqlalchemy import Column, Integer, String, Date, DateTime

from database import Base

class Promocode(Base):
    __tablename__ = "promocodes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    validity_period = Column(Date)
    month = Column(Integer)
    limit = Column(Integer, default=100)
    status = Column(String(50)) # Accessible, Inactive, over
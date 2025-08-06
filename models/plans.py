from sqlalchemy import Column, Integer, String, Text, Float

from database import Base

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Integer)
    price = Column(Float)
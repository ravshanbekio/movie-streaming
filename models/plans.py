from sqlalchemy import Column, Integer, String, Text, Float

from database import Base

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    description = Column(Text)
    price = Column(Float)
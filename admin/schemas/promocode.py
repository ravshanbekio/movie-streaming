from pydantic import BaseModel
from datetime import date
from enum import Enum

class PromocodeStatus(str, Enum):
    ACCESSIBLE = "accessible"
    INACTIVE = "inactive"
    OVER = "over"

class PromocodeResponse(BaseModel):
    id: int
    name: str
    validity_period: date
    limit: int  
    status: PromocodeStatus
    
class CreatePromocodeForm(BaseModel):
    name: str
    validity_period: date
    month: int
    limit: int
    
class UpdatePromocodeForm(BaseModel):
    id: int
    name: str
    validity_period: date
    month: int
    limit: int   
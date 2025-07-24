from pydantic import BaseModel
from enum import Enum

class PromocodeStatus(str, Enum):
    ACCESSIBLE = "accessible"
    INACTIVE = "inactive"
    OVER = "over"

class PromocodeResponse(BaseModel):
    id: int
    name: str
    validity_period: int
    limit: int
    status: PromocodeStatus
    
class CreatePromocodeForm(BaseModel):
    name: str
    validity_period: int
    limit: int
    
class UpdatePromocodeForm(BaseModel):
    id: int
    name: str
    validity_period: int
    limit: int   
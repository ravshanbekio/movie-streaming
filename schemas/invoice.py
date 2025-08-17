# schemas/payme.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Dict, Any
from enum import Enum
from datetime import date

# Unified request structure
class PaymeRequest(BaseModel):
    id: Optional[int]
    method: Literal[
        "CheckPerformTransaction", "CreateTransaction", "PerformTransaction",
        "CancelTransaction", "CheckTransaction", "GetStatement", "ChangePassword"
    ]
    params: Dict[str, Any]  # Raw, will be parsed based on `method`

# Error response format
class PaymeError(BaseModel):
    code: int
    message: Dict[str, str]

# Generic response
class PaymeResponse(BaseModel):
    id: Optional[int]
    result: Optional[Dict[str, Any]] = None
    error: Optional[PaymeError] = None

# -------- Specific Param Schemas -------- #

class CheckPerformTransactionParams(BaseModel):
    amount: int
    account: Dict[str, str]

class CreateTransactionParams(BaseModel):
    id: str
    time: int
    amount: int
    account: Dict[str, str]

class PerformTransactionParams(BaseModel):
    id: str

class CancelTransactionParams(BaseModel):
    id: str
    reason: int

class CheckTransactionParams(BaseModel):
    id: str

class GetStatementParams(BaseModel):
    from_: int = Field(..., alias="from")
    to: int
    
class ChangePasswordParams(BaseModel):
    password: str
    
# Click request
class ClickRequest(BaseModel):
    order_id: int
    amount: int
    
class PaymentMethods(str, Enum):
    PAYME = 'payme'
    CLICK = 'click'
    
class OrderResponse(BaseModel):
    id: int
    subcription_end_date: Optional[date]
    
class SubscriptionType(str, Enum):
    BUY = "buy"
    UPDATE = "update"

class CreateOrderForm(BaseModel):
    plan_id: int
    promocode: Optional[str]
    method: Optional[PaymentMethods] = None
    type: SubscriptionType
    
    @field_validator("method", mode="before")
    def replace_zero_date(cls, value):
        if value in ("", None):
            return None
        return value
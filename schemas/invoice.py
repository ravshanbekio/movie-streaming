# schemas/payme.py

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any

# Unified request structure
class PaymeRequest(BaseModel):
    id: Optional[int]
    method: Literal[
        "CheckPerformTransaction", "CreateTransaction", "PerformTransaction",
        "CancelTransaction", "CheckTransaction", "GetStatement"
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

class CreateOrderForm(BaseModel):
    plan_id: int
    promocode: Optional[str]
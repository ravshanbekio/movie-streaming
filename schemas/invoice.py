from pydantic import BaseModel
from typing import Optional

class CreateInvoiceForm(BaseModel):
    order_id: str = '123456'
    total_price: int
    
    
class CreateOrderForm(BaseModel):
    plan_id: int
    promocode: Optional[str]
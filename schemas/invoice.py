from pydantic import BaseModel

class CreateInvoiceForm(BaseModel):
    order_id: str = '123456'
    total_price: int
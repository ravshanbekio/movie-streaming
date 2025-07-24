from fastapi import APIRouter, Depends
from models.user import User
from schemas.invoice import CreateInvoiceForm
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse


invoice_router = APIRouter(tags=["Invoice"])


@invoice_router.post("/create_invoice")
async def create_invoice(form: CreateInvoiceForm, current_user: User = Depends(get_current_active_user)):
    return CreatedResponse()
import os
from fastapi import APIRouter, Depends
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from dotenv import load_dotenv

from database import get_db
from crud import get_all, get_one, create, change, delete
from models.user import User
from models.order import Order
from models.plans import Plan
from models.promocode import Promocode
from admin.schemas.promocode import PromocodeStatus
from schemas.invoice import CreateInvoiceForm, CreateOrderForm
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse, CustomResponse

load_dotenv()

invoice_router = APIRouter(tags=["Invoice"])
MERCHANT_ID = os.getenv("MERCHANT_ID")

@invoice_router.post("/create_order")
async def create_order(form: CreateOrderForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    promocode = None
    if form.promocode:
        checkPromocodeExists = await get_one(db=db, model=Promocode, filter_query=and_(Promocode.name==form.promocode, Promocode.status==PromocodeStatus.ACCESSIBLE))
        if not checkPromocodeExists:
            return CustomResponse(status_code=400, detail="Bunday promokod mavjud emas")
        promocode = checkPromocodeExists.id
        
    checkPlanExists = await get_one(db=db, model=Plan, filter_query=(Plan.id==form.plan_id))
    if not checkPlanExists:
        return CustomResponse(status_code=400, detail="Bunday plan mavjud emas")
    
    checkUsernotInOrders = await get_one(db=db, model=Order, filter_query=(Order.user_id==current_user.id))
    if checkUsernotInOrders:
        return CustomResponse(status_code=400, detail="Obuna allaqachon rasmiylashtirilgan!")

    amount = 0 if promocode is not None else checkPlanExists.price
    payload = {
        "user_id":current_user.id,
        "promocode_id":promocode,
        "total_price":amount,
        "created_at":datetime.now()
    }
    order = await create(db=db, model=Order, form=payload, id=True)
    
    if promocode is not None:
        promocode_payload = {
            "limit": checkPromocodeExists.limit - 1
        }
        updatePromocodeLimit = await change(db=db, model=Promocode, filter_query=(Promocode.id==promocode), form=promocode_payload)
        refreshedPromocode = await get_one(db=db, model=Promocode, filter_query=(Promocode.id==promocode))
        if refreshedPromocode.limit == 0:
            updatePromocodeStatus = await change(db=db, model=Promocode, filter_query=(Promocode.id==promocode), form={"status":PromocodeStatus.OVER})

    return {
        "total_price":amount,
        "payme_link":f"https://checkout.paycom.uz?merchant={MERCHANT_ID}&amount={amount}&account[order_id]={order}"
        
    }

@invoice_router.post("/create_invoice")
async def create_invoice(form: CreateInvoiceForm):
    return CreatedResponse()
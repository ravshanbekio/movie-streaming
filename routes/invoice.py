import os
from fastapi import APIRouter, Depends, Request
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from dotenv import load_dotenv
# Payment integrations
from paytechuz.gateways.payme import PaymeGateway
from integrations.payme.webhook import CustomPaymeWebhookHandler

from database import get_db, get_sync_db
from crud import get_all, get_one, create, change, delete
from models.user import User
from models.order import Order
from models.plans import Plan
from models.promocode import Promocode
from admin.schemas.promocode import PromocodeStatus
from schemas.invoice import PaymeRequest, CreateOrderForm
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse, CustomResponse

load_dotenv()

invoice_router = APIRouter(tags=["Invoice"])
MERCHANT_ID = os.getenv("MERCHANT_ID")
PAYME_KEY = os.getenv("PAYME_KEY")
PAYME_TEST_KEY = os.getenv("PAYME_TEST_KEY")

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
    
    if form.month not in [1, 3, 6, 12]:
        return CustomResponse(status_code=400, detail="Noto'g'ri obuna sanasi kiritildi")

    amount = 0 if promocode is not None else checkPlanExists.price * form.month
    payload = {
        "user_id":current_user.id,
        "promocode_id":promocode,
        "amount":amount,
        "created_at":datetime.now(),
        "next_payment_date": datetime.today().date() + timedelta(days=30),
        "subscription_date":form.month,
        "subcription_end_date":datetime.today.date() + timedelta(months=form.month)
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
            
    payme = PaymeGateway(
        payme_id=MERCHANT_ID,
        payme_key=PAYME_KEY,
        is_test_mode=False
    )
    payme_link = payme.create_payment(
        id=order,
        amount=amount,
        return_url="https://google.com"
    )

    return {
        "total_price":amount,
        "payme_link":payme_link
    }

@invoice_router.post("/create_invoice")
async def create_invoice(request: Request, form: PaymeRequest, db: Session = Depends(get_sync_db)):
    handler = CustomPaymeWebhookHandler(
        db=db,
        payme_id=MERCHANT_ID,
        payme_key=PAYME_TEST_KEY,
        account_model=Order,
        account_field="order_id",
        amount_field="amount"
    )
    return await handler.handle_webhook(request)
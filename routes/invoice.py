import os
from fastapi import APIRouter, Depends, Request
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
# Payment integrations
from paytechuz.gateways.payme import PaymeGateway
from paytechuz.gateways.click import ClickGateway
from integrations.payme.webhook import CustomPaymeWebhookHandler

from database import get_db, get_sync_db
from crud import get_all, get_one, create, change, delete
from models.user import User
from models.order import Order
from models.plans import Plan
from models.promocode import Promocode
from models.payment_token import PaymentToken
from admin.schemas.promocode import PromocodeStatus
from schemas.invoice import PaymeRequest, CreateOrderForm, ClickRequest
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse, CustomResponse

load_dotenv()

invoice_router = APIRouter(tags=["Invoice"])
# Payme credentials
MERCHANT_ID = os.getenv("MERCHANT_ID")
PAYME_KEY = os.getenv("PAYME_KEY")
PAYME_TEST_KEY = os.getenv("PAYME_TEST_KEY")
# Click credentials
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID")
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID")
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID")
SECRET_KEY = os.getenv("SECRET_KEY")

@invoice_router.get("/click/token_callback")
async def click_token_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    if data.get("status") == "success":
        user_id = int(data["merchant_user_id"])
        card_token = data["card_token"]

        existing = db.query(PaymentToken).filter_by(user_id=user_id).first()
        if existing:
            existing.token = card_token
        else:
            db.add(ClickToken(user_id=user_id, token=card_token))
        db.commit()
        return {"status": "ok"}
    
    return {"status": "failed"}


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
        "subcription_end_date":datetime.today().date() + relativedelta(months=form.month)
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
            
    link = None
    if form.method == "payme":
        payme = PaymeGateway(
            payme_id=MERCHANT_ID,
            payme_key=PAYME_KEY,
            is_test_mode=False
        )
        link = payme.create_payment(
            id=order,
            amount=amount,
            return_url="http://161.97.113.186/click/token_callback"
        )
    elif form.method == "click":
        click = ClickGateway(
            service_id=CLICK_SERVICE_ID,
            merchant_id=CLICK_MERCHANT_ID,
            merchant_user_id=CLICK_MERCHANT_USER_ID,
            secret_key=SECRET_KEY,
            is_test_mode=False
        )
        click_data = click.create_payment(
            id=order,
            amount=amount,
            return_url="http://161.97.113.186/click/token_callback",
        )
        link = click_data['payment_url']

    return {
        "total_price":amount,
        "link":link
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

@invoice_router.post("/click/create_invoice")
async def create_click_invoice(request: Request, form: ClickRequest, db: Session = Depends(get_sync_db)):
    handler = CustomClickWebhookHandler(
        db=db,
        service_id=CLICK_SERVICE_ID,
        merchant_id=CLICK_MERCHANT_ID,
        secret_key=SECRET_KEY,
        account_model=Order
    )
    return await handler.handle_webhook(request)
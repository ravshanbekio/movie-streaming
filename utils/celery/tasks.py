from .celery_app import celery
from datetime import date, timedelta
from sqlalchemy import and_

from crud import get_all, change
from database import AsyncSessionLocal
from models.promocode import Promocode
from models.order import Order
from admin.schemas.promocode import PromocodeStatus

@celery.task
async def check_expired_items():
    db = AsyncSessionLocal()
    today = date.today().date()
    promocodes = await get_all(db=db, model=Promocode, filter_query=and_(Promocode.validity_period <= today, Promocode.status!=PromocodeStatus.INACTIVE))
    
    if promocode['data']:
        for promocode in promocode['data']:
            await change(db=db, model=Promocode, filter_query=(Promocode.id==promocode.id), form={"status":PromocodeStatus.INACTIVE})
            
            await change(db=db, model=Order, filter_query=and_(Order.promocode_id==promocode.id, Order.status=="free"), form={"status":"paid"})
            print(f"[CELERY] Marked promocode {promocode.id} as expired")
            
@celery.task()
async def updateFreePaymentDate():
    db = AsyncSessionLocal()
    today = date.today().date()
    next_payment_date = today + timedelta(days=30)
    
    orders = get_all(db=db, model=Order, filter_query=and_(Order.status=="free", Order.next_payment_date==today))
    
    for order in order["data"]:
        await change(db=db, model=Order, filter_query=(Order.id==order.id), form={"next_payment_date":next_payment_date})
        
    print("Free order's updated")

@celery.task()
async def chargeAutopayment():
    db = AsyncSessionLocal()
    today = date.today().date()
    next_payment_date = today + timedelta(days=30)
    
    orders = get_all(db=db, model=Order, filter_query=and_(Order.status=="paid", Order.next_payment_date==today))
    
    for order in order["data"]:
        print("Simulating autopayment")

        await change(db=db, model=Order, filter_query=(Order.id==order.id), form={"next_payment_date":next_payment_date})
        
    print("Monthly Payments charged")
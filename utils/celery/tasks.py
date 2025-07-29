from .celery_app import celery
from datetime import date, timedelta, datetime

from database import SessionLocal
from models.promocode import Promocode
from models.order import Order
from admin.schemas.promocode import PromocodeStatus

@celery.task
def check_expired_items():
    db = SessionLocal()
    today = datetime.today().date()
    promocodes = db.query(Promocode).filter(Promocode.validity_period <= today, Promocode.status!=PromocodeStatus.INACTIVE).all()
        
    for promocode in promocode:
        db.query(Promocode).filter(Promocode.id==promocode.id).update({
            "status":PromocodeStatus.INACTIVE
        })
        
        db.query(Order).filter(Order.promocode_id==promocode.id, Order.status=="free").update({
            "status":"paid"
        })
        db.commit()
        print(f"[CELERY] Marked promocode {promocode.id} as expired")
            
@celery.task()
def updateFreePaymentDate():
    db = SessionLocal()
    today = datetime.today().date()
    next_payment_date = today + timedelta(days=30)
    
    orders = db.query(Order).filter(Order.status=="free", Order.next_payment_date==today).all()
    
    for order in orders:
        db.query(Order).filter(Order.id==order.id).update({
            "next_payment_date":next_payment_date
        })
        db.commit()        
    print("Free order's updated")

@celery.task()
def chargeAutopayment():
    db = SessionLocal()
    today = datetime.today().date()
    next_payment_date = today + timedelta(days=30)
    
    orders = db.query(Order).filter(Order.status=="paid", Order.next_payment_date==today).all()
    
    for order in orders:
        print("Simulating autopayment")

        db.query(Order).filter(Order.id==order.id).update({
            "next_payment_date":next_payment_date
        })
        db.commit()
        
    print("Monthly Payments charged")
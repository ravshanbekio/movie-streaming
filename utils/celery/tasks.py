from .celery_app import celery
from datetime import date, timedelta, datetime

from database import SessionLocal
from models.promocode import Promocode
from models.order import Order
from models.user import User
from admin.schemas.promocode import PromocodeStatus

@celery.task
def check_expired_items():
    db = SessionLocal()
    today = datetime.today().date()
    promocodes = db.query(Promocode).filter(Promocode.validity_period <= today, Promocode.status!=PromocodeStatus.INACTIVE).all()
    
    for promocode in promocodes:
        db.query(Promocode).filter(Promocode.id==promocode.id).update({
            "status":PromocodeStatus.INACTIVE
        })
        
        db.query(Order).filter(Order.promocode_id==promocode.id, Order.status=="free").update({
            "status":"paid"
        })
        db.commit()
        print(f"[CELERY] Marked promocode {promocode.id} as expired")
    
@celery.task()
def updateExpiredOrders():
    db = SessionLocal()
    today = datetime.today().date()
    
    orders = db.query(Order).filter(Order.subcription_end_date < today).all()
    for order in orders:
        db.query(User).filter(User.id==order.user_id).update({
            "subscribed":False
        })
        db.commit()
        
        db.query(Order).filter(Order.id==order.id).delete()
        db.commit()
        
    print("Deleted expired orders.")
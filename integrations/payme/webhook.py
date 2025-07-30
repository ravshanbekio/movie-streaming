from paytechuz.integrations.fastapi import PaymeWebhookHandler
from models.order import Order
from models.user import User

class CustomPaymeWebhookHandler(PaymeWebhookHandler):
    def successfully_payment(self, params, transaction):
        # Handle successful payment
        order = self.db.query(Order).filter(Order.id == transaction.account_id).first()
        order.status = "paid"
        self.db.commit()
        
        user = self.db.query(User).filter(User.id==order.user_id).update({
            "subscribed":True
        })
        self.db.commit()

    def cancelled_payment(self, params, transaction):
        # Handle cancelled payment
        order = self.db.query(Order).filter(Order.id == transaction.account_id).first()
        order.status = "cancelled"
        self.db.commit()
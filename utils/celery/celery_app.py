from celery import Celery

celery = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["utils.celery.tasks"]
)

celery.conf.beat_schedule = {
    "check-expired-every-day": {
        "task": "utils.celery.tasks.check_expired_items",
        "schedule": 86400.0,
    },
    "update-expired-orders":{
        "task":"utils.celery.tasks.updateExpiredOrders",
        "schedule":86400.0,
    },
    "delete-unfinished-orders":{
        "task":"utils.celery.tasks.deleteUnfinishedOrders",
        "schedule":5
    }
}
celery.conf.timezone = 'UTC'

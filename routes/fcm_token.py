from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database import get_db
from crud import create, get_one, get_all, change
from models.fcm_token import FCMToken
from models.notification import Notification
from models.user import User
from schemas.fcm_token import TokenCreate, BroadcastForm
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse, UpdatedResponse
from utils.notification import send_to_all_users

fcm_token_router = APIRouter(tags=["Notification"])

@fcm_token_router.get("/get_notifications")
async def get_notifications(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user), page: int = 1, limit: int = 25):
    return await get_all(db=db, model=Notification, order_by=(desc(Notification.created_at)), page=page, limit=limit)

@fcm_token_router.post("/fcm_token")
async def fcm_token(form: TokenCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    checkUserExists = await get_one(db=db, model=User, filter_query=(User.id==form.user_id))
    if not checkUserExists:
        return CustomResponse(status_code=400, detail="Bunday foydalanuvchi mavjud emas")
    
    checkFCMTokenExists = await get_one(db=db, model=FCMToken, filter_query=(FCMToken.user_id==form.user_id))
    if checkFCMTokenExists:
        payload = {
            "token": form.token
        }
        await change(db=db, model=FCMToken, filter_query=(FCMToken.user_id==form.user_id), form=payload)
        return UpdatedResponse()
    else:
        create_token = await create(db=db, model=FCMToken, form=form.model_dump())
        return CreatedResponse()

@fcm_token_router.post("/broadcast")
async def broadcast(form: BroadcastForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    get_all_tokens = await get_all(db=db, model=FCMToken, page=1, limit=500)
    token_list = [t.token for t in get_all_tokens['data']]
    results = send_to_all_users(token_list, form.title, form.body)
    return results
    
    payload = {
        "title":form.title,
        "body":form.body,
        "created_at":datetime.now()
    }
    await create(db=db, model=Notification, form=payload)
    return {"status":"done"}
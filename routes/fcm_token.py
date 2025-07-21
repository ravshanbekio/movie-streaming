from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from crud import create, get_one, get_all
from models.fcm_token import FCMToken
from models.user import User
from schemas.fcm_token import TokenCreate, BroadcastForm
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse
from utils.notification import send_to_all_users

fcm_token_router = APIRouter(tags=["Notification"])

@fcm_token_router.post("/fcm_token")
async def fcm_token(form: TokenCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    checkUserExists = await get_one(db=db, model=User, filter_query=(User.id==form.user_id))
    if not checkUserExists:
        return CustomResponse(status_code=400, detail="Bunday foydalanuvchi mavjud emas")
    
    create_token = await create(db=db, model=FCMToken, form=form.model_dump())
    return CreatedResponse()

@fcm_token_router.post("/broadcast")
async def broadcast(form: BroadcastForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    get_all_tokens = await get_all(db=db, model=FCMToken, page=1, limit=500)
    token_list = [t.token for t in get_all_tokens['data']]
    results = send_to_all_users(token_list, form.title, form.body)
    return {"status":"done"}
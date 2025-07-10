from fastapi import APIRouter, Depends
from sqlalchemy import desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database import get_db
from crud import get_all, get_one, create
from models.user import User
from models.content import Content
from models.user_history import UserHistory
from admin.schemas.content import ContentStatusEnum, ContentSchema, ContentType
from utils.auth import get_current_active_user
from utils.exceptions import CustomResponse

content_router = APIRouter(tags=["Contents"], prefix="/user")

@content_router.get("/contents/all")
async def get_contents(status: ContentSchema = None, page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), 
                       current_user: User = Depends(get_current_active_user)):
    filters = []
    order_by = desc(Content.created_at)
    if status:
        if status == ContentSchema.shows:
            filters.append(Content.type==ContentType.show)
        if status == ContentSchema.films:
            filters.append(Content.type==ContentType.film)
        if status == ContentSchema.ongoing:
            filters.append(Content.status==ContentStatusEnum.ongoing)
        if status == ContentSchema.stopped:
            filters.append(Content.status==ContentStatusEnum.stopped)
        if status == ContentSchema.premium:
            filters.append(Content.subscription_status==True)

    filter_query = and_(*filters) if filters else None
    return await get_all(db=db, model=Content, filter_query=filter_query, order_by=order_by, page=page, limit=limit)

@content_router.get("/content/one")
async def get_content_by_id(content_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    content = await get_one(db=db, model=Content, filter_query=(Content.content_id==content_id))
    if not content:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot mavjud emas")
    
    getUserHistory = await get_one(db=db, model=UserHistory, filter_query=and_(UserHistory.user_id==current_user.id, UserHistory.content_id==content_id))
    if not getUserHistory:
        form = {
            "user_id":current_user.id,
            "content_id":content_id,
            "created_at":datetime.now()
        }
        await create(db=db, model=UserHistory, form=form)
    
    return content
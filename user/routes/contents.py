from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List

from database import get_db
from crud import get_all, get_one, create
from models.user import User
from models.genre import Genre
from models.content import Content, movie_genre_association
from models.user_history import UserHistory
from admin.schemas.content import ContentStatusEnum, ContentSchema, ContentType
from utils.auth import get_current_active_user
from utils.exceptions import CustomResponse

content_router = APIRouter(tags=["Contents"], prefix="/user")

@content_router.get("/contents/all")
async def get_contents(status: ContentSchema = None, page: int = 1, limit: int = 25,
                       subscription_status: bool = None, content_type: ContentType = None, genre_ids: List[int] = Query(default=[]),
                       db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    filters = []
    order_by = desc(Content.created_at)
    if status:
        if status == ContentSchema.ongoing:
            filters.append(Content.status==ContentStatusEnum.ongoing)
        if status == ContentSchema.stopped:
            filters.append(Content.status==ContentStatusEnum.stopped)
            
    if subscription_status:
        filters.append(Content.subscription_status==subscription_status)
        
    if content_type:
        filters.append(Content.type==content_type)
    
    if genre_ids:
        for genre_id in genre_ids:
            genre = await get_one(db=db, model=Genre, filter_query=(Genre.genre_id==genre_id))
            if not genre:
                return CustomResponse(status_code=400, detail=f"Bunday ID'dagi janr mavjud emas [{genre_id}]")
            
        get_content_by_genre = await get_all(db=db, model=movie_genre_association, filter_query=(movie_genre_association.c.genre_id.in_(genre_ids)), page=1, limit=100)
        content_ids = [row for row in get_content_by_genre['data']]
        
        filters.append(Content.content_id.in_(content_ids))
        
    if current_user.country != "998":
        limit = 2

    filter_query = and_(*filters) if filters else None
    return await get_all(db=db, model=Content, filter_query=filter_query, order_by=order_by, page=page, limit=limit)


@content_router.get("/content/one")
async def get_content_by_id(content_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    content = await get_one(db=db, model=Content, filter_query=(Content.content_id==content_id))
    if not content:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot mavjud emas")
    
    return content
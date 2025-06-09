from fastapi import APIRouter, Depends, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, date

from database import get_db
from crud import get_all, get_one, create, change, remove
from models.user import User
from models.genre import Genre
from models.content import Content
from schemas.content import ContentResponse
from utils.exceptions import CreatedResponse, UpdatedResponse, DeletedResponse, CustomResponse
from utils.auth import get_current_active_user

content_router = APIRouter(tags=["Content"])

MIN_DATE = date(1970, 1, 1)

@content_router.post("/content/create_movie")
async def create_content(
    title: str = Form(description="Sarlavha", repr=False),
    description: Optional[str] = Form(None, description="Batafsil ma'lumot", repr=False),
    genre: Optional[int] = Form(None, description="Janr", repr=False),
    release_date: Optional[date] = Form(None, description="Chiqarilgan sana", repr=False),
    dubbed_by: Optional[str] = Form(None, description="Dublaj qilingan studio nomi", repr=False),
    thumbnail: UploadFile = File(description="Rasm", repr=False),
    content_url: UploadFile = File(description="Media fayl", repr=False),
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_genre = await get_one(db=db, model=Genre, filter_query=(Genre.genre_id==genre))
    if not get_genre:
        return CustomResponse(status_code=400, detail="Bunday janr mavjud emas")
    
    if release_date:
        if release_date < MIN_DATE:
            return CustomResponse(status_code=400, detail="Sana 1970-yildan past bo'lmasligi kerak")

    form = {
        "title":title,
        "description":description,
        "genre":genre,
        "release_date":release_date,
        "dubbed_by":dubbed_by,
        "thumbnail":thumbnail,
        "content_url":content_url,
        "created_at":datetime.now()
    }

    await create(db=db, model=Content, form=form)
    return CreatedResponse()


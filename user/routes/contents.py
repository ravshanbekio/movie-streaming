from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from crud import get_all, get_one
from models.user import User
from models.content import Content
from utils.auth import get_current_active_user

content_router = APIRouter(tags=["Contents"], prefix="/user")

@content_router.get("/contents/all")
async def get_contents(status: str = None, page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), 
                       current_user: User = Depends(get_current_active_user)):
    # filters = []
    # if status:
    #     filters.append(Content)
    return await get_all(db=db, model=Content, page=page, limit=limit)
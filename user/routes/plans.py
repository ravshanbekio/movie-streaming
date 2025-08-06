from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from crud import get_one, get_all
from database import get_db
from models.plans import Plan
from models.user import User
from utils.auth import get_current_active_user
from utils.exceptions import CustomResponse

plan_router = APIRouter(tags=["Plans"])

@plan_router.get("/get_plans")
async def get_plans(page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return await get_all(db=db, model=Plan, page=page, limit=limit)

@plan_router.get("/get_plan")
async def get_plan(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    data = await get_one(db=db, model=Plan, filter_query=(Plan.id==id))
    if not data:
        return CustomResponse(status_code=400, detail="Hech qanday obuna tarifi topilmadi")
    
    return data
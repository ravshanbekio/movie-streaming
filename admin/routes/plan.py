from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from crud import get_all, get_one, create, remove
from utils.auth import get_current_active_user
from models.user import User
from models.plans import Plan
from admin.schemas.user import AdminRole
from admin.schemas.plan import CreatePlanForm
from utils.exceptions import CreatedResponse, UpdatedResponse, CustomResponse, DeletedResponse
from utils.pagination import Page


plan_router = APIRouter(tags=["Plans"])

@plan_router.get("/get_plans")
async def get_plans(page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return await get_all(db=db, model=Plan, page=page, limit=limit, order_by=desc(Plan.id))

@plan_router.post("/create_plan")
async def create_plan(form: CreatePlanForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    checkPlanTitleExists = await get_one(db=db, model=Plan, filter_query=(Plan.title==form.title))
    if checkPlanTitleExists:
        return CustomResponse(status_code=400, detail="Bunday nomdagi obuna turi allaqachon mavjud")
    
    await create(db=db, model=Plan, form=form.model_dump())
    return CreatedResponse()

@plan_router.delete("/delete_plan")
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    checkPlanExists = await get_one(db=db, model=Plan, filter_query=(Plan.id==plan_id))
    if not checkPlanExists:
        return CustomResponse(status_code=400, detail="Bunday obuna turi mavjud emas")
    
    remove(db=db, model=Plan, filter_query=(Plan.id==plan_id))
    return DeletedResponse()
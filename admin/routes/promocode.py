from fastapi import APIRouter, Depends
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from crud import create, change, get_all, get_one, remove
from models.user import User
from models.promocode import Promocode
from admin.schemas.user import AdminRole
from admin.schemas.promocode import PromocodeResponse, CreatePromocodeForm, UpdatePromocodeForm, PromocodeStatus
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse, UpdatedResponse, DeletedResponse, CustomResponse
from utils.pagination import Page

promocode_router = APIRouter(tags=["Promocode"])

@promocode_router.get("/get_promocodes")
async def get_promocodes(page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Page[PromocodeResponse]:
    return await get_all(db=db, model=Promocode, page=page, limit=limit)

@promocode_router.post("/create_promocode")
async def create_promocode(form: CreatePromocodeForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    checkPromocodeNameExists = await get_one(db=db, model=Promocode, filter_query=(Promocode.name==form.name))
    if checkPromocodeNameExists:
        return CustomResponse(status_code=400, detail="Ushbu nom ostida promokod mavjud")
    
    # if form.validity_period < :
    #     return CustomResponse(status_code=400, detail="Noto'g'ri vaqt kiritildi")
    
    payload = {
        "name":form.name,
        "validity_period":form.validity_period,
        "limit":form.limit,
        "status":PromocodeStatus.ACCESSIBLE
    }
    await create(db=db, model=Promocode, form=payload)
    return CreatedResponse()

@promocode_router.put("/update_promocode")
async def update_promocode(form: UpdatePromocodeForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    checkPromocodeExists = await get_one(db=db, model=Promocode, filter_query=(Promocode.id==form.id))
    if not checkPromocodeExists:
        return CustomResponse(status_code=400, detail="Bunday promokod mavjud emas")

    checkPromocodeNameExists = await get_one(db=db, model=Promocode, filter_query=and_(Promocode.name==form.name, Promocode.id!=form.id))
    if checkPromocodeNameExists:
        return CustomResponse(status_code=400, detail="Ushbu nom ostida promokod mavjud")
    
    # if form.validity_period < 0:
    #     return CustomResponse(status_code=400, detail="Noto'g'ri vaqt kiritildi")
    
    await change(db=db, model=Promocode, filter_query=(Promocode.id==form.id), form=form.model_dump())
    return UpdatedResponse()

@promocode_router.delete("/delete_promocode")
async def delete_promocode(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    checkPromocodeExists = await get_one(db=db, model=Promocode, filter_query=(Promocode.id==id))
    if not checkPromocodeExists:
        return CustomResponse(status_code=400, detail="Bunday promokod mavjud emas")
    
    await remove(db=db, model=Promocode, filter_query=(Promocode.id==id))
    return DeletedResponse()
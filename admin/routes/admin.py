from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from crud import get_all, get_one, create, change, remove
from database import get_db
from models.user import User
from schemas.user import UserAuthForm, UserResponse, UserCreateForm, UserUpdateForm
from utils.auth import get_password_hash, get_current_active_user
from utils.exceptions import CreatedResponse, UpdatedResponse, CustomResponse, DeletedResponse
from utils.auth import pwd_context, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from utils.pagination import Page

admin_router = APIRouter(tags=["Admin"])

@admin_router.get("/admin/all", summary="Barcha adminlarni olish")
async def get_all_users(role: str = None, page: int = 1, limit: int = 25, \
                        db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Page[UserResponse]:
    if current_user.role != "admin" or current_user.role != "owner":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    filters = []
    if role:
        filters.append(User.role == role)
    
    filter_query = and_(*filters, User.status.in_(["admin","owner"])) if filters else None
    return await get_all(db=db, model=User, filter_query=filter_query, page=page, limit=limit)

@admin_router.get("/admin/profile")
async def get_current_user_data(current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    return await get_one(db=db, model=User, filter_query=(User.id==current_user.id))


# @admin_router.get("/users/{phone_number}", summary="Foydalanuvchi haqida ma'lumot olish")
# async def get_user(phone_number: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> UserResponse:
#     return await get_one(db=db, model=User, filter_query=(User.phone_number==phone_number))

@admin_router.post("/admin/create", summary="Admin yaratish")
async def create_user(form: UserCreateForm, db: AsyncSession = Depends(get_db)) -> UserCreateForm:
    get_user = await get_one(db=db, model=User, filter_query=(User.phone_number==form.phone_number))
    if get_user:
        return CustomResponse(status_code=400, detail="Ushbu telefon raqam mavjud")
    if len(form.password) < 6:
        return CustomResponse(status_code=400, detail="Parol 6ta belgidan kam bo'lmasligi kerak")
    
    form.password = get_password_hash(form.password)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form.phone_number}, expires_delta=access_token_expires
    )
    data = {
        "phone_number":form.phone_number,
        "password": form.password,
        "role": form.role,
        "joined_at":datetime.now(),
        "refresh_token":access_token
    }
    await create(db=db, model=User, form=data)
    return ORJSONResponse(status_code=201, content={"token":access_token})

@admin_router.put("/admin/update", summary="Admin ma'lumotlarini o'zgartirish")
async def update_user(form: UserUpdateForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    get_user = await get_one(db=db, model=User, filter_query=(User.id==form.id))
    if not get_user:
        return CustomResponse(status_code=400, detail="Bunday admin mavjud emas")
    
    if form.phone_number:
        get_user = await get_one(db=db, model=User, filter_query=and_(User.phone_number==form.phone_number, User.id!=form.id))
        if get_user:
            return CustomResponse(status_code=400, detail="Ushbu telefon raqam mavjud")
    else:
        form.phone_number = get_user.phone_number

    if form.password:
        if len(form.password) < 6:
            return CustomResponse(status_code=400, detail="Parol 6ta belgidan kam bo'lmasligi kerak")
        form.password = get_password_hash(form.password)
    else:
        form.password = get_user.password
    
    await change(db=db, model=User, filter_query=(User.id==form.id), form=form.model_dump(exclude={"id"}))
    return UpdatedResponse()

@admin_router.delete("/admin/delete", summary="Adminni o'chirish")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin" or current_user.role != "owner":
        raise CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_user = await get_one(db=db, model=User, filter_query=(User.id==user_id))
    if not get_user:
        return CustomResponse(status_code=400, detail="Bunday admin mavjud emas")
    
    await remove(db=db, model=User, filter_query=(User.id==user_id))
    return DeletedResponse()
from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from crud import get_all, get_one, create, change, remove
from database import get_db
from models.user import User
from schemas.user import UserAuthForm, UserResponse, UserCreateForm, UserUpdateForm
from admin.schemas.user import AdminRole
from utils.auth import get_password_hash, get_current_active_user
from utils.exceptions import CreatedResponse, UpdatedResponse, CustomResponse, DeletedResponse
from utils.auth import pwd_context, create_access_token, ACCESS_TOKEN_EXPIRE_DAYS
from utils.pagination import Page

admin_router = APIRouter(tags=["Admin"])

@admin_router.get("/admin/all", summary="Barcha adminlarni olish")
async def get_all_users(role: str = None, page: int = 1, limit: int = 25, \
                        db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Page[UserResponse]:
    if current_user.role not in AdminRole:
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


@admin_router.delete("/admin/delete", summary="Adminni o'chirish")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        raise CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_user = await get_one(db=db, model=User, filter_query=(User.id==user_id))
    if not get_user:
        return CustomResponse(status_code=400, detail="Bunday admin mavjud emas")
    
    await remove(db=db, model=User, filter_query=(User.id==user_id))
    return DeletedResponse()
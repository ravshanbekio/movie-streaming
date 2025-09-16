import random
from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from crud import get_one, create, change
from database import get_db
from models.user import User
from models.user_token import UserToken
from schemas.user import PhoneNumberForm, UserCreateForm, UserUpdateForm, ConfirmSMSForm, ResetPasswordForm
from utils.auth import get_password_hash, get_current_active_user
from utils.exceptions import CustomResponse, UpdatedResponse
from utils.auth import create_access_token, ACCESS_TOKEN_EXPIRE_DAYS, get_password_hash
from utils.sms_integration import send_sms

user_router = APIRouter(tags=["User"])

@user_router.post("/user/create", summary="Admin yaratish")
async def create_user(form: UserCreateForm, db: AsyncSession = Depends(get_db)) -> UserCreateForm:
    get_user = await get_one(db=db, model=User, filter_query=(User.phone_number==form.phone_number))
    if get_user:
        return CustomResponse(status_code=400, detail="Ushbu telefon raqam mavjud")
    if len(form.password) < 6:
        return CustomResponse(status_code=400, detail="Parol 6ta belgidan kam bo'lmasligi kerak")
    
    form.password = get_password_hash(form.password)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": form.phone_number}, expires_delta=access_token_expires
    )
    code = random.randint(111111, 999999)
    data = {
        "first_name":form.first_name,
        "last_name":form.last_name,
        "phone_number":form.phone_number,
        "password": form.password,
        "role": form.role,
        "country":form.country,
        "joined_at":datetime.now(),
        "code": code
    }
    user = await create(db=db, model=User, form=data, id=True)
    await create(db=db, model=UserToken, form={"user_id":user, "access_token":access_token, "created_at":datetime.now()})
    await send_sms(phone_number=form.phone_number, code=code)
    return ORJSONResponse(status_code=201, content={"token":access_token})


@user_router.put("/admin/update", summary="Admin ma'lumotlarini o'zgartirish")
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

@user_router.put("/confirm_sms")
async def confirm_sms(form: ConfirmSMSForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    get_user = await get_one(db=db, model=User, filter_query=(User.id==current_user.id))
    if get_user.code != int(form.code):
        return False
    return {
        "status":"success",
        "user": {
              "id":get_user.id,
              "first_name": get_user.first_name,
              "last_name": get_user.last_name,
              "phone_number":get_user.phone_number,
              "role": get_user.role,
              "joined_at": get_user.joined_at
            }
        }

@user_router.post("/resend_sms")
async def resend_sms(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    code = random.randint(111111, 999999)
    await change(db=db, model=User, filter_query=(User.id==current_user.id), form={"code":code})
    await send_sms(phone_number=current_user.phone_number, code=code)
    return CustomResponse(status_code=200, detail="SMS qayta yuborildi")

@user_router.post("/forgot_password")
async def forgot_password(form: PhoneNumberForm, db: AsyncSession = Depends(get_db)):
    checkUserExists = await get_one(db=db, model=User, filter_query=(User.phone_number==form.phone_number))
    if not checkUserExists:
        return CustomResponse(status_code=200, detail="Foydalanuvchi topilmadi")
    
    code = random.randint(111111, 999999)
    await change(db=db, model=User, filter_query=(User.id==checkUserExists.id), form={"code":code})
    await send_sms(phone_number=checkUserExists.phone_number, code=code)
    return CustomResponse(status_code=200, detail="Yangi parol qo'yish uchun SMS kod yuborildi")

@user_router.put("/reset_password")
async def reset_password(form: ResetPasswordForm, db: AsyncSession = Depends(get_db)):
    checkUserExists = await get_one(db=db, model=User, filter_query=(User.phone_number==form.phone_number))
    if not checkUserExists:
        return CustomResponse(status_code=200, detail="Loginda xatolik")
    
    password = get_password_hash(form.password)
    await change(db=db, model=User, filter_query=(User.phone_number==form.phone_number), form={"password":password})
    return {"status":"success"}
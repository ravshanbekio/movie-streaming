from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy import select, update, insert
from sqlalchemy.orm import joinedload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.user import User
from models.user_token import UserToken
from models.order import Order
from schemas.user import Token, UserAuthForm
from schemas.invoice import OrderResponse
from datetime import timedelta, datetime

from utils.auth import pwd_context, create_access_token, ACCESS_TOKEN_EXPIRE_DAYS

auth_router = APIRouter(tags=["Token"])


@auth_router.post("/token")
async def token(form_data: UserAuthForm, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).where(User.phone_number == form_data.phone_number, User.status == "active").options(
        joinedload(User.order).load_only(Order.id, Order.subcription_end_date), with_loader_criteria(Order, Order.status=="paid")))
    user = query.scalars().first()
    
    if not user:
        raise HTTPException(status_code=200, detail="Login yoki parolda xatolik")
    
    if form_data.password is not None:
        if user:
            is_validate_password = pwd_context.verify(form_data.password, user.password)
        else:
            is_validate_password = False
        if not is_validate_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login yoki parolda xatolik",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.phone_number}, expires_delta=access_token_expires
    )
    await db.execute(insert(UserToken).values({
        UserToken.user_id: user.id,
        UserToken.access_token: access_token,
        UserToken.created_at: datetime.now()
    }))
    await db.commit()
    order_data = None

    if user and user.order:
        order_data = OrderResponse.model_validate({
            "id": user.order.id,
            "subcription_end_date": user.order.subcription_end_date
        })
        
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role":user.role if user.role else None,
        "order": order_data
    }
    
    
@auth_router.post("/refresh_token", response_model=Token)
async def refresh_token(db: AsyncSession = Depends(get_db), token: str = None):
    query = await db.execute(select(User).where(User.refresh_token == token))
    user = query.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Token error",
        )

    # if not token_has_expired(token):
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Token has not expired",
    #     )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.phone_number},
        expires_delta=access_token_expires
    )
    await db.execute(update(User).where(User.id == user.id).values({
        User.refresh_token: access_token
    }))
    await db.commit()
    return {
            "access_token": access_token, 
            "token_type": "bearer",
            "role":user.role
        }

# @auth_router.get("/profile")
# def get_profile(current_user: User = Depends(get_current_active_user)):
#     return {
#         "username":current_user.username,
#         "fullname":current_user.fullname,
#         "filial_id":current_user.filial_id,
#         "role":current_user.role,
#         "id": current_user.id,
#         "phone":current_user.phone,
#         "status": current_user.status,
#         "phone2":current_user.phone2
#     }
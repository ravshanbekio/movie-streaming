from pydantic import BaseModel
from typing import Optional
from .invoice import OrderResponse

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    order: Optional[OrderResponse]

class TokenData(BaseModel):
    phone_number: str

class UserResponse(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: str
    subscribed: Optional[bool]
    role: Optional[str]

class UserAuthForm(BaseModel):
    phone_number: str
    password: Optional[str]

class UserCreateForm(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    password: str
    country: str
    role: str = "user"

class UserUpdateForm(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    role: Optional[str]
    password: Optional[str]
    
class ConfirmSMSForm(BaseModel):
    phone_number: str
    code: str
    
class PhoneNumberForm(BaseModel):
    phone_number: str
    
class ResetPasswordForm(BaseModel):
    phone_number: str
    password: str
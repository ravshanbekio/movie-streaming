import random
import os
import httpx
import aiohttp
from dotenv import load_dotenv
from eskiz.client import AsyncClient
from sqlalchemy import and_

from crud import get_one, change
from database import AsyncSessionLocal
from models.user import User

load_dotenv()

EMAIL = os.getenv("ESKIZ_EMAIL")
PASSWORD = os.getenv("ESKIZ_PASSWORD")

LOGIN_URL = "https://notify.eskiz.uz/api/auth/login"

LOGIN_URL = "https://notify.eskiz.uz/api/auth/login"

async def send_sms(phone_number: str, code: int):
    db = AsyncSessionLocal()
    try:
        data = {
            "email": EMAIL,
            "password": PASSWORD
        }

        async with httpx.AsyncClient() as client:
            # login request
            resp = await client.post(LOGIN_URL, data=data)
            resp.raise_for_status()
            token = resp.json()["data"]["token"]

            # send SMS
            url = "https://notify.eskiz.uz/api/message/sms/send"
            headers = {"Authorization": f"Bearer {token}"}

            sms_data = {
                "mobile_phone": phone_number,
                "message": f"Aniduble ilovasida ro'yxatdan o'tish uchun kod: {code}",
                "from": "4546",
                "callback_url": ""
            }

            response = await client.post(url, headers=headers, data=sms_data)
            response.raise_for_status()

            return response.json()
    finally:
        db.close()
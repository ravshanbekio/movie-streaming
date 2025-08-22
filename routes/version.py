import ast
from fastapi import APIRouter, Depends
from models.user import User
from schemas.version import VersionForm
from utils.auth import get_current_active_user

version_router = APIRouter(tags=["Version Router"])


@version_router.get("/get_app_version")
async def get_app_version(current_user: User = Depends(get_current_active_user)):
    text = None
    with open("version.txt","r") as version:
        text = version.readline()
    return ast.literal_eval(text)

@version_router.post("/update_version")
async def update_version(form: VersionForm, current_user: User = Depends(get_current_active_user)):
    response = None
    with open("version.txt", "w") as version:
        version.write(str(form.model_dump()))

    with open("version.txt","r") as version:
        response = version.readline()
        
    return ast.literal_eval(response)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crud import get_all, get_one, create, change, remove
from database import get_db
from utils.auth import get_current_active_user
from models.user import User
from models.genre import Genre
from admin.schemas.genre import GenreResponse, GenreCreateForm, GenreUpdateForm
from utils.exceptions import CreatedResponse, UpdatedResponse, CustomResponse, DeletedResponse
from utils.pagination import Page

genre_router = APIRouter(tags=["Genre"])

@genre_router.get("/genres/all")
async def get_all_genres(page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Page[GenreResponse]:
    return await get_all(db=db, model=Genre, page=page, limit=limit)

@genre_router.post("/genres/create")
async def create_genre(form: GenreCreateForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_genre = await get_one(db=db, model=Genre, filter_query=(Genre.title==form.title))
    if get_genre:
        return CustomResponse(status_code=400, detail="Bunday janr mavjud")
    
    await create(db=db, model=Genre, form=form.model_dump())
    return CreatedResponse()

@genre_router.put("/genres/update")
async def update_genre(form: GenreUpdateForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_genre = await get_one(db=db, model=Genre, filter_query=(Genre.genre_id==form.genre_id))
    if not get_genre:
        return CustomResponse(status_code=400, detail="Bunday janr mavjud emas")
    
    get_genre = await get_one(db=db, model=Genre, filter_query=(Genre.title==form.title))
    if get_genre:
        return CustomResponse(status_code=400, detail="Bunday janr mavjud")
    
    await change(db=db, model=Genre, filter_query=(Genre.genre_id==form.genre_id), form=form.model_dump())
    return UpdatedResponse()

@genre_router.delete("/genres/delete")
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizday yetarli huquqlar yo'q")
    
    get_genre = await get_one(db=db, model=Genre, filter_query=(Genre.genre_id==genre_id))
    if not get_genre:
        return CustomResponse(status_code=400, detail="Bunday janr mavjud emas")
    
    await remove(db=db, model=Genre, filter_query=(Genre.genre_id==genre_id))
    return DeletedResponse()
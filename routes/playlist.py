from fastapi import APIRouter, Depends, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database import get_db
from crud import get_all, get_one, create, change, remove
from models.user import User
from models.content import Content
from models.content import Playlist
from schemas.content import ContentResponse
from schemas.playlist import PlaylistResponse
from utils.exceptions import CreatedResponse, UpdatedResponse, DeletedResponse, CustomResponse
from utils.auth import get_current_active_user
from utils.compressor import save_image
from utils.pagination import Page

playlist_router = APIRouter(tags=["Playlist"])

PLAYLIST_UPLOAD_DIR = "playlist_thumbnails"

@playlist_router.get("/playlists/all")
async def get_playlists(page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Page[PlaylistResponse]:
    return await get_all(db=db, model=Playlist, page=page, limit=limit)

@playlist_router.get("/playlists/all/content")
async def get_playlist_contents(playlist_id: int, page: int = 1, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Page[ContentResponse]:
    return await get_all(db=db, model=Content, filter_query=(Content.playlist_id==playlist_id), page=page, limit=limit)

@playlist_router.post("/playlists/create")
async def create_playlist(
    title: str = Form(description="Sarlavha", repr=False),
    description: str = Form(None, description="Batafsil ma'lumot", repr=False),
    thumbnail: UploadFile = File(description="Rasm", repr=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_title = await get_one(db=db, model=Playlist, filter_query=(Playlist.title==title))
    if get_title:
        return CustomResponse(status_code=400, detail="Bunday playlist mavjud")
    
    form = {
        "title":title,
        "description":description,
        "thumbnail":thumbnail,
        "created_at":datetime.today().date()
    }

    if thumbnail:
        save_thumbnail = await save_image(PLAYLIST_UPLOAD_DIR, thumbnail)
        form["thumbnail"] = save_thumbnail['path']
     
    await create(db=db, model=Playlist, form=form)
    return CreatedResponse()

@playlist_router.put("/playlists/update")
async def update_playlist(
    playlist_id: int = Form(description="Playlist ID", repr=False),
    title: str = Form(None, description="Sarlavha", repr=False),
    description: str = Form(None, description="Batafsil ma'lumot", repr=False),
    thumbnail: UploadFile = File(None, description="Rasm", repr=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_playlist = await get_one(db=db, model=Playlist, filter_query=(Playlist.playlist_id==playlist_id))
    if not get_playlist:
        return CustomResponse(status_code=400, detail="Bunday playlist mavjud emas")
    
    get_playlist = await get_one(db=db, model=Playlist, filter_query=(Playlist.playlist_id!=playlist_id, Playlist.title==title))
    if get_playlist:
        return CustomResponse(status_code=400, detail="Bunday playlist mavjud")
    
    form = {}
    if title:
        form["title"] = title
    if description:
        form["description"] = description
    if thumbnail:
        save_thumbnail = await save_image(PLAYLIST_UPLOAD_DIR, thumbnail)
        form["thumbnail"] = save_thumbnail["path"]

    await change(db=db, model=Playlist, filter_query=(Playlist.playlist_id==playlist_id))
    return UpdatedResponse()

@playlist_router.delete("/playlist/delete")
async def delete_playlist(playlist_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_playlist = await get_one(db=db, model=Playlist, filter_query=(Playlist.playlist_id==playlist_id))
    if not get_playlist:
        return CustomResponse(status_code=400, detail="Bunday playlist mavjud emas")
    
    await remove(db=db, model=Playlist, filter_query=(Playlist.playlist_id==playlist_id))
    return DeletedResponse()
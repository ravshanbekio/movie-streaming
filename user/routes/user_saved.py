from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database import get_db
from crud import get_all, get_one, create, remove
from models.user import User
from models.content import Content
from models.episode import Episode
from models.user_saved import UserSaved
from user.schemas.user_saved import UserSavedResponse, UserSavedForm
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse, DeletedResponse, CustomResponse
from utils.pagination import Page

saved_router = APIRouter(tags=["User saved"], prefix="/user")

@saved_router.get("/saved/all")
async def get_user_saved(page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    limit = limit
    if current_user.country != "998":
        limit = 2
        
    get_user_saved = await get_all(db=db, model=UserSaved, filter_query=(UserSaved.user_id==current_user.id), 
                                   options=[joinedload(UserSaved.content), joinedload(UserSaved.episode)],
                                   order_by=desc(UserSaved.id), 
                                   unique=True,
                                   page=page, limit=limit)
    grouped = {}

    for item in get_user_saved["data"]:
        user_saved_id = item.id
        content = item.content
        episode = item.episode

        if not content:
            continue  # skip if content is missing

        content_id = content.content_id

        # Use (content_id, user_history_id) as key to allow multiple history items for same content
        key = (content_id, user_saved_id)

        if key not in grouped:
            grouped[key] = {
                "id": user_saved_id,
                "content": {
                    "content_id": content.content_id,
                    "title": content.title,
                    "description": content.description,
                    "content_url": content.content_url,
                    "thumbnail": content.thumbnail,
                    "content_duration": content.content_duration,
                    "type": content.type,
                    "episodes": []
                }
            }

        if episode:
            grouped[key]["content"]["episodes"].append({
                "id": episode.id,
                "season": episode.seasion,
                "episode": episode.episode,
                "episode_video": episode.episode_video,
                "episode_thumbnail": episode.episode_thumbnail,
                "duration": str(episode.duration)
            })
    
    return {
        "total_pages": get_user_saved["total_pages"],
        "current_page": get_user_saved["current_page"],
        "limit": get_user_saved["limit"],
        "data": list(grouped.values())
    }    
    
@saved_router.post("/saved/create")
async def create_user_saved(form: UserSavedForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    form = {
        "user_id":current_user.id,
        "content_id":form.content_id,
        "episode_id":form.episode_id,
        "created_at":datetime.now()
    }
    get_content = await get_one(db=db, model=Content, filter_query=(Content.content_id==form['content_id']))
    if not get_content:
        return CustomResponse(status_code=400, detail=f"Bunday ID'dagi kontent mavjud emas [{form['content_id']}]")
        
    if form['episode_id']:
        get_episode = await get_one(db=db, model=Episode, filter_query=(Episode.id==form['episode_id'], Episode.content_id==form['content_id']))
        if not get_episode:
            return CustomRespone(status_code=400, detail=f"Bunday ID'dagi serial mavjud emas [{form['episode_id']}]")
    
    await create(db=db, model=UserSaved, form=form)
    return CreatedResponse()

@saved_router.delete("/saved/delete")
async def delete_user_saved(saved_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    get_user_saved = await get_one(db=db, model=UserSaved, filter_query=(UserSaved.id==saved_id))
    if not get_user_saved:
        return CustomResponse(status_code=400, detail=f"Bunday ID'dagi saqlash topilmadi [{saved_id}]")
    
    await remove(db=db, model=UserSaved, filter_query=(UserSaved.id==saved_id))
    return DeletedResponse()
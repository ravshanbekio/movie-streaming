from fastapi import APIRouter, Depends
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database import get_db
from crud import get_all, get_one, create, change
from models.user import User
from models.user_history import UserHistory
from models.content import Content
from models.episode import Episode
from admin.schemas.content import ContentType
from user.schemas.watch_history import HistoryResponse, HistoryForm
from utils.auth import get_current_active_user
from utils.exceptions import CreatedResponse, UpdatedResponse, CustomResponse
from utils.pagination import Page

watch_history_router = APIRouter(tags=["Watch history"], prefix="/user")

@watch_history_router.get("/get_history")
async def get_history(page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    limit = limit
    if current_user.country != "998":
        limit = 2
        
    get_user_history = await get_all(db=db, model=UserHistory, filter_query=(UserHistory.user_id==current_user.id), options=[joinedload(UserHistory.content), 
                                                                        joinedload(UserHistory.episode)], order_by=(UserHistory.id.desc()),
                                    page=page, limit=limit, unique=True)
    
    grouped = {}

    for item in get_user_history["data"]:
        user_history_id = item.id
        user_history_duration = str(item.duration)
        content = item.content
        episode = item.episode

        if not content:
            continue  # skip if content is missing

        content_id = content.content_id

        # Use (content_id, user_history_id) as key to allow multiple history items for same content
        key = (content_id, user_history_id)

        if key not in grouped:
            grouped[key] = {
                "id": user_history_id,
                "duration": user_history_duration,
                "content": {
                    "content_id": content.content_id,
                    "title": content.title,
                    "description": content.description,
                    "original_content": content.original_content,
                    "converted_content": content.converted_content,
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
                "original_episode": episode.original_episode,
                "converted_episode": episode.converted_episode,
                "episode_thumbnail": episode.episode_thumbnail,
                "duration": str(episode.duration)
            })        
    return {
        "total_pages": get_user_history["total_pages"],
        "current_page": get_user_history["current_page"],
        "limit": get_user_history["limit"],
        "data": list(grouped.values())
    }

@watch_history_router.post("/create_history")
async def create_history(form: HistoryForm, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    payload = {
        "user_id": current_user.id,
        "content_id":form.content_id,
        "episode_id":form.episode_id,
        "duration":form.duration,
        "created_at":datetime.now()
    }
    
    get_content = await get_one(db=db, model=Content, filter_query=(Content.content_id==form.content_id))
    if not get_content:
        return CustomResponse(status_code=400, detail=f"Bunday ID'dagi kontent mavjud emas [{form.content_id}]")
    
    if form.episode_id:
        if get_content.type == ContentType.film:
            return CustomResponse(status_code=400, detail="Bu kontent turi kino")
        
        get_episode = await get_one(db=db, model=Episode, filter_query=and_(Episode.content_id==form.content_id, Episode.id==form.episode_id))
        if not get_episode:
            return CustomResponse(status_code=400, detail=f"Bunday ID'dagi serial mavjud emas [{form.episode_id}]")
        
    get_user_history = await get_one(db=db, model=UserHistory, filter_query=and_(UserHistory.user_id==current_user.id, UserHistory.content_id==form.content_id))
    if get_user_history:
        payload = {
            "episode_id":form.episode_id,
            "duration": form.duration
        }
        await change(db=db, model=UserHistory, filter_query=and_(UserHistory.user_id==current_user.id, UserHistory.content_id==form.content_id), form=payload)
        return UpdatedResponse()
    else:
        await create(db=db, model=UserHistory, form=payload)
        return CreatedResponse()
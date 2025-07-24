from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import desc, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from collections import defaultdict

from database import get_db
from crud import get_all, get_one, create, change
from models.user import User
from models.content import Content
from models.episode import Episode
from models.user_history import UserHistory
from utils.auth import get_current_active_user
from utils.exceptions import CustomResponse

episode_router = APIRouter(tags=["User Episode"], prefix="/user")

@episode_router.get("/episodes/all")
async def get_episodes(content_id: int, page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    content = await get_one(db=db, model=Content, filter_query=and_(Content.content_id==content_id, Content.converted_content.isnot(None)), options=[joinedload(Content.episodes)])
    if not content:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot topilmadi")
    
    grouped = defaultdict(list)
    for episode in content.episodes:
        grouped[episode.seasion].append({
            "id": episode.id,
            "episode": episode.episode,
            "original_episode": episode.original_episode,
            "converted_episode":episode.converted_episode,
            "episode_thumbnail": episode.episode_thumbnail,
            "duration": episode.duration,
            "created_at": episode.created_at.isoformat(),
        })
    return JSONResponse(status_code=200, content=[
        {
        "seasion":int(key),
        "episodes":value
    }
    for key, value in grouped.items()
    ])
    

@episode_router.get("/episode/one")
async def get_episode(episode_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    getEpisode = await get_one(db=db, model=Episode, filter_query=(Episode.id==episode_id))
    if not getEpisode:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot mavjud emas")
    
    previous_episode = await get_one(db=db, model=Episode, filter_query=(
        (Episode.content_id==getEpisode.content_id) &
        (Episode.seasion==getEpisode.seasion) &
        (Episode.episode==getEpisode.episode - 1)
    )
        )
    
    next_episode = await get_one(db=db, model=Episode, filter_query=(
        (Episode.content_id==getEpisode.content_id) &
        (Episode.seasion==getEpisode.seasion) &
        (Episode.episode==getEpisode.episode + 1)
    )
        )
    
    return {
        "episode_data":getEpisode,
        "previous_episode":previous_episode.id if previous_episode else None,
        "next_episode": next_episode.id if next_episode else None
    }
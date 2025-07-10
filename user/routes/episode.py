from fastapi import APIRouter, Depends
from sqlalchemy import desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database import get_db
from crud import get_all, get_one, create, change
from models.user import User
from models.episode import Episode
from models.user_history import UserHistory
from utils.auth import get_current_active_user
from utils.exceptions import CustomResponse

episode_router = APIRouter(tags=["User Episode"], prefix="/user")

# @episode_router.get("/episodes/all")
# async def get_episodes(content_id: int, page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
#     content = await get_one(db=db, model=Content, filter_query=(Content.content_id==content_id), options=[joinedload(Content.episodes)])
#     if not content:
#         return CustomResponse(status_code=400, detail="Bunday ma'lumot topilmadi")
    

@episode_router.get("/episode/one")
async def get_episode(episode_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    getEpisode = await get_one(db=db, model=Episode, filter_query=(Episode.id==episode_id))
    if not getEpisode:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot mavjud emas")
    
    getUserHistory = await get_one(db=db, model=UserHistory, filter_query=and_(UserHistory.user_id==current_user.id,
                                                                               UserHistory.content_id==getEpisode.content_id
                                                                               ))
    if not getUserHistory:
        form = {
            "user_id":current_user.id,
            "content_id":getEpisode.content_id,
            "episode_id":episode_id,
            "created_at":datetime.now()
        }
        await create(db=db, model=UserHistory, form=form)
    
    form = {
        "episode_id":episode_id
    }
    await change(db=db, model=UserHistory, filter_query=and_(UserHistory.user_id==current_user.id, UserHistory.content_id==getEpisode.content_id), form=form)
    return getEpisode
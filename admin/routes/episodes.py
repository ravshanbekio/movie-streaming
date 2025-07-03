from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from botocore.exceptions import BotoCoreError, ClientError

from database import get_db
from crud import get_all, get_one, create, change, remove
from models.user import User
from models.episode import Episode
from models.content import Content
from admin.schemas.episode import EpisodeResponse
from admin.schemas.user import AdminRole
from utils.exceptions import CreatedResponse, DeletedResponse, CustomResponse
from utils.auth import get_current_active_user
from utils.compressor import upload_thumbnail_to_r2
from utils.r2_utils import r2, R2_BUCKET, R2_PUBLIC_ENDPOINT

episode_router = APIRouter(tags=["Episodes"], prefix="/episodes")
THUMBNAIL_UPLOAD_DIR = "episodes"

@episode_router.get("/all")
async def get_all_episodes(content_id: int, seasion: str, page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    return await get_all(db=db, model=Episode, filter_query=and_(Episode.content_id==content_id, Episode.seasion==seasion.lower()))

@episode_router.post("/create_episode")
async def create_new_episode(
    background_task: BackgroundTasks,
    seasion: str = Form(description="Seasion", repr=False),
    content_id: int = Form(description="Content ID", repr=False),
    episode: str = Form(description="Episode", repr=False),
    episode_video: UploadFile = File(description="Episode", repr=False),
    episode_thumbnail: UploadFile = Form(description="Episode thumbnail"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    get_content = await get_one(db=db, model=Content, filter_query=(Content.content_id==content_id))
    if not get_content:
        return CustomResponse(status_code=400, detail="Bunday kontent mavjud emas")

    try:
        #Cloudga yuklash
        r2.upload_fileobj(
            Fileobj=episode_video.file,
            Bucket=R2_BUCKET,
            Key=f"episodes/{episode_video.filename}",
            ExtraArgs={'ContentType': episode_video.content_type}
        )

        form = {
        "content_id":content_id,
        "seasion":seasion,
        "episode":episode.lower(),
        "episode_video":f"{R2_PUBLIC_ENDPOINT}/{R2_BUCKET}/episodes/{episode_video.filename}",
        "episode_thumbnail":episode_thumbnail
        }

        if episode_thumbnail:
            save_thumbnail = await upload_thumbnail_to_r2(episode_thumbnail)
            form["episode_thumbnail"] = save_thumbnail

        await create(db=db, model=Episode, form=form)
        return CreatedResponse()

    except (BotoCoreError, ClientError) as e:
        return CustomResponse(status_code=400, detail=str(e))

@episode_router.delete("/delete_episode")
async def delete_episode(episode_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")

    get_episode = await get_one(db=db, model=Episode, filter_query=(Episode.id==episode_id))
    if not get_episode:
        return CustomResponse(status_code=400, detail="Bunday episode mavjud emas")

    await remove(db=db, model=Episode, filter_query=(Episode.id==episode_id))
    return DeletedResponse()
from fastapi import APIRouter, Depends, Form, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from botocore.exceptions import BotoCoreError, ClientError
from collections import defaultdict
from datetime import datetime
from typing import Optional
from redis import Redis
from rq import Queue

from database import get_db
from crud import get_all, get_one, create, change, remove
from models.user import User
from models.episode import Episode
from models.content import Content
from admin.schemas.episode import EpisodeResponse
from admin.schemas.user import AdminRole
from utils.exceptions import CreatedResponse, DeletedResponse, CustomResponse, UpdatedResponse
from utils.auth import get_current_active_user
from utils.compressor import upload_thumbnail_to_r2, AVAILABLE_IMAGE_FORMATS, AVAILABLE_VIDEO_FORMATS
from utils.r2_utils import r2, R2_BUCKET, R2_PUBLIC_ENDPOINT
from utils.rq_tasks import rq_convert_and_upload


redis = Redis()
task_queue = Queue("video", connection=redis)

episode_router = APIRouter(tags=["Episode"], prefix="/episodes")
THUMBNAIL_UPLOAD_DIR = "episodes"

@episode_router.get("/all")
async def get_all_episode(content_id: int, seasion: str = None, page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    content = await get_one(db=db, model=Content, filter_query=(Content.content_id==content_id), options=[joinedload(Content.episodes)])
    if not content:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot topilmadi")
    
    grouped = defaultdict(list)
    for episode in content.episodes:
        grouped[episode.seasion].append({
            "id": episode.id,
            "episode": episode.episode,
            "original_episode": episode.original_episode,
            "converted_episode": episode.converted_episode,
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

@episode_router.post("/create_episode")
async def create_new_episode(
    seasion: int = Form(description="Seasion", repr=False),
    content_id: int = Form(description="Content ID", repr=False),
    episode: int = Form(description="episode", repr=False),
    episode_video: UploadFile = File(description="Episode video", repr=False),
    episode_thumbnail: UploadFile = Form(description="Episode thumbnail"),
    duration: str = Form(description="Episode duration"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    get_content = await get_one(db=db, model=Content, filter_query=(Content.content_id==content_id))
    if not get_content:
        return CustomResponse(status_code=400, detail="Bunday kontent mavjud emas")

    try:
        if episode_video.content_type not in AVAILABLE_VIDEO_FORMATS:
            return CustomResponse(status_code=400, detail=f"Video formati noto'g'ri {episode_video.content_type}")
            
        #Cloudga yuklash
        r2.upload_fileobj(
            Fileobj=episode_video.file,
            Bucket=R2_BUCKET,
            Key=f"episodes/{episode_video.filename}",
            ExtraArgs={'ContentType': episode_video.content_type}
        )
        episode_folder = f"{R2_PUBLIC_ENDPOINT}/episodes/{episode_video.filename}"

        form = {
        "content_id":content_id,
        "seasion":seasion,
        "episode":episode,
        "original_episode":f"{episode_folder}",
        "episode_thumbnail":episode_thumbnail,
        "duration":duration,
        "created_at":datetime.now()
        }

        if episode_thumbnail:
            save_thumbnail = await upload_thumbnail_to_r2(episode_thumbnail)
            form["episode_thumbnail"] = save_thumbnail

        created_episode = await create(db=db, model=Episode, form=form, id=True)
        task_queue.enqueue(rq_convert_and_upload, 
                           db="mysql+asyncmy://root:Madaminov27!@localhost:3306/movie_db", id=created_episode,
                           input_url=episode_folder, filename=episode_video.filename, output_prefix="episodes", job_timeout=15000)
        return CreatedResponse()

    except (BotoCoreError, ClientError) as e:
        return CustomResponse(status_code=400, detail=str(e))
    
@episode_router.put("/update_episode")
async def update_episode(
    episode_id: int = Form(description="Episode ID", repr=False),
    seasion: Optional[int] = Form(None, description="Seasion", repr=False),
    content_id: Optional[int] = Form(None, description="Content ID", repr=False),
    episode: Optional[int] = Form(None, description="episode", repr=False),
    episode_thumbnail: Optional[UploadFile] = Form(None, description="Episode thumbnail"),
    duration: Optional[str] = Form(None, description="Episode duration"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    get_episode = await get_one(db=db, model=Episode, filter_query=(Episode.id==episode_id))
    if not get_episode:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot mavjud emas")

    form = {}
    if seasion:
        form['seasion'] = seasion
    if content_id:
        get_content = await get_one(db=db, model=Content, filter_query=(Content.content_id==content_id))
        if not get_content:
            return CustomResponse(status_code=400, detail="Bunday kontent mavjud emas")
        
        form['content_id'] = content_id
    if episode:
        form['episode'] = episode
    if duration:
        form['duration'] = duration
    if episode_thumbnail:
        save_thumbnail = await upload_thumbnail_to_r2(episode_thumbnail)
        form["episode_thumbnail"] = save_thumbnail

    await change(db=db, model=Episode, filter_query=(Episode.id==episode_id), form=form)
    return UpdatedResponse()

@episode_router.delete("/delete_episode")
async def delete_episode(episode_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")

    get_episode = await get_one(db=db, model=Episode, filter_query=(Episode.id==episode_id))
    if not get_episode:
        return CustomResponse(status_code=400, detail="Bunday epizod mavjud emas")

    await remove(db=db, model=Episode, filter_query=(Episode.id==episode_id))
    return DeletedResponse()
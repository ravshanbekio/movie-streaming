from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from crud import get_all, get_one, create, change, remove
from models.user import User
from models.episode import Episode
from admin.schemas.episode import EpisodeResponse
from utils.exceptions import CreatedResponse, UpdatedResponse, DeletedResponse, CustomResponse
from utils.auth import get_current_active_user
from utils.compressor import save_image
from utils.r2_utils import r2, R2_BUCKET, R2_PUBLIC_ENDPOINT
from utils.tasks import verify_upload_background
from utils.pagination import Page, paginate

episode_router = APIRouter(tags=["Episodes"], prefix="/episodes")
THUMBNAIL_UPLOAD_DIR = "episodes"

@episode_router.get("/all")
async def get_all_episodes(content_id: int, seasion: str, page: int = 1, limit: int = 25, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    return await get_all(db=db, model=Episode, filter_query=(Episode.content_id==content_id, Episode.seasion==seasion.lower()))

@episode_router.post("/generate_upload_url")
def generate_upload_url(episode_video: UploadFile = File(description="Episode")):
    episode_object_key = f"episodes/raw/{episode_video.filename}"

    episode_presigned_url = r2.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": R2_BUCKET,
            "Key": episode_object_key,
            "ContentType": episode_video.content_type
        },
        ExpiresIn=3600  # 1 hour
    )

    return {
        # Episode 
        "episode_upload_url": episode_presigned_url,
        "episode_object_key": episode_object_key,
        "episode_public_url": f"{R2_PUBLIC_ENDPOINT}/{episode_object_key}",
    }


@episode_router.post("/create_episode")
async def create_new_episode(
    background_task: BackgroundTasks,
    seasion: str = Form(description="Seasion", repr=False),
    episode: str = Form(description="Episode", repr=False),
    episode_object_key: str = Form(description="Episode object KEY", repr=False),
    episode_thumbnail: UploadFile = Form(description="Episode thumbnail"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar mavjud emas")
    
    episode_public_url = f"{R2_PUBLIC_ENDPOINT}/{episode_object_key}"
    form = {
        "seasion":seasion,
        "episode":episode.lower(),
        "episode_video":episode_public_url,
        "episode_thumbnail":episode_thumbnail
    }

    if episode_thumbnail:
        save_thumbnail = await save_image(THUMBNAIL_UPLOAD_DIR, episode_thumbnail)
        form['episode_thumbnail'] = save_thumbnail['path']

    created_episode = await create(db=db, model=Episode, form=form, id=True)
    background_task.add_task(
        verify_upload_background,
        db=db,
        model=Episode,
        filter_query=(Episode.id==created_episode),
        content_object_key=episode_object_key
        )
    return CreatedResponse()
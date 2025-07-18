from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import ORJSONResponse
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, date
from botocore.exceptions import BotoCoreError, ClientError
from redis import Redis
from rq import Queue


from database import get_db
from crud import get_all, get_one, create, change, remove
from models.user import User
from models.genre import Genre
from models.content import Content, movie_genre_association
from models.episode import Episode
from admin.schemas.content import ContentResponse, ContentDetailResponse, ContentSchema, ContentStatusEnum, ContentType
from admin.schemas.user import AdminRole
from utils.exceptions import CreatedResponse, UpdatedResponse, DeletedResponse, CustomResponse
from utils.auth import get_current_active_user
from utils.r2_utils import r2, R2_BUCKET, R2_PUBLIC_ENDPOINT
from utils.compressor import upload_thumbnail_to_r2, AVAILABLE_VIDEO_FORMATS, AVAILABLE_IMAGE_FORMATS
from utils.pagination import Page
from utils.rq_tasks import convert_and_upload

redis = Redis()
task_queue = Queue("video", connection=redis)

content_router = APIRouter(tags=["Content"], prefix="/contents")
MIN_DATE = date(1970, 1, 1)

@content_router.get("/all")
async def get_all_contents(page: int = 1, limit: int = 25, status: ContentSchema = None, search: str = None, subscription_status: bool = None,
                           content_type: ContentType = None, genre_id: int = None, latest: bool = None,
                           db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> Page[ContentResponse]:
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    filter_query = []
    order_by = None
    if status:
        if status == ContentSchema.ongoing:
            filter_query.append(Content.status==ContentStatusEnum.ongoing)
        if status == ContentSchema.stopped:
            filter_query.append(Content.status==ContentStatusEnum.stopped)
    
    if subscription_status is not None:
        filter_query.append(Content.subscription_status==subscription_status)
        
    if content_type:
        filter_query.append(Content.type==content_type)
        
    if genre_id:
        get_content_by_genre = await get_all(db=db, model=movie_genre_association, filter_query=(movie_genre_association.c.genre_id==genre_id), page=1, limit=100)
        content_ids = [row for row in get_content_by_genre['data']]
        
        filter_query.append(Content.content_id.in_(content_ids))
        
    if latest:
        order_by = (desc(Content.created_at))

    if search:
        filter_query.append(or_(Content.title.like(f"%{search}%"), Content.description.like(f"%{search}%")))

    filters = and_(*filter_query) if filter_query else None
    return await get_all(db=db, model=Content, filter_query=filters, options=[joinedload(Content.genre_data), selectinload(Content.episodes)], 
                         order_by=order_by,
                         unique=True, page=page, limit=limit)

@content_router.get("/one")
async def get_one_content(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> ContentDetailResponse:
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    data = await get_one(db=db, model=Content, filter_query=and_(Content.content_id==id), options=[joinedload(Content.genre_data)])
    if not data:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot mavjud emas")
    
    return data

@content_router.post("/create_content")
async def create_content(
    background_task: BackgroundTasks,
    title: str = Form(description="Sarlavha", repr=False),
    description: Optional[str] = Form(None, description="Batafsil ma'lumot", repr=False),
    genre: List[int] = Form(None, description="Janr", repr=False),
    release_date: Optional[date] = Form(None, description="Chiqarilgan sana", repr=False),
    dubbed_by: Optional[str] = Form(None, description="Dublaj qilingan studio nomi", repr=False),
    status: ContentStatusEnum = Form(description="Status", repr=False),
    subscription_status: bool = Form(description="Obunalik kontent", repr=False),
    thumbnail: UploadFile = File(description="Rasm", repr=False),
    content: Optional[UploadFile] = File(None, description="Content", repr=False),
    trailer: Optional[UploadFile] = File(None, description="Trailer Object KEY", repr=False),
    content_duration: Optional[str] = Form(None, description="Content duration", repr=False),
    trailer_duration: Optional[str] = Form(None, description="Trailer duration"),
    type: ContentType = Form(description="Content type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
    ):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_genre = await get_all(db=db, model=Genre, filter_query=(Genre.genre_id.in_(genre)))
    if len(get_genre['data']) != len(genre):
        return CustomResponse(status_code=400, detail="Bunday janr mavjud emas")

    if release_date:
        if release_date < MIN_DATE:
            return CustomResponse(status_code=400, detail="Sana 1970-yildan past bo'lmasligi kerak")
    content_folder = None
    trailer_folder = None
    try:
        if content:
            if content.content_type not in AVAILABLE_VIDEO_FORMATS: 
                return CustomResponse(status_code=400, detail=f"Video formati noto'g'ri {content.content_type}")
                
            # Cloudga animeni yuklash
            r2.upload_fileobj(
                Fileobj=content.file,
                Bucket=R2_BUCKET,
                Key=f"contents/{content.filename}",
                ExtraArgs={'ContentType': content.content_type}
            )
            
            content_folder = f"{R2_PUBLIC_ENDPOINT}/contents/{content.filename}"
            task_queue.enqueue(convert_and_upload, input_url=content_folder, filename=content.filename, output_prefix="contents", job_timeout=5000)

        # Cloudga trailerni yuklash (agar bor bo'lsa)
        if trailer:
            if trailer.content_type not in AVAILABLE_VIDEO_FORMATS:
                return CustomResponse(status_code=400, detail=f"Trailer formati noto'g'ri {trailer.content_type}")
                
            r2.upload_fileobj(
            Fileobj=trailer.file,
            Bucket=R2_BUCKET,
            Key=f"trailers/{trailer.filename}",
            ExtraArgs={'ContentType': trailer.content_type}
        )   
            trailer_folder = f"{R2_PUBLIC_ENDPOINT}/trailers/{trailer.filename}"
            task_queue.enqueue(convert_and_upload, input_url=trailer_folder, filename=trailer.filename, output_prefix="trailers", job_timeout=600)
        
        form = {
            "uploader_id":current_user.id,
            "title":title,
            "description":description,
            "release_date":release_date,
            "dubbed_by":dubbed_by,
            "status":status,
            "subscription_status":subscription_status,
            "content_duration":content_duration,
            "trailer_duration":trailer_duration,
            "type":type,
            "thumbnail":None,
            "content_url":f"{content_folder}/",
            "trailer_url":f"{trailer_folder}/" if trailer else None,
            "created_at":datetime.now()
        }

        if thumbnail:
            save_thumbnail = await upload_thumbnail_to_r2(thumbnail)
            form["thumbnail"] = save_thumbnail

        created_content = await create(db=db, model=Content, form=form, id=True)

        for genre in get_genre['data']:
            await create(db=db, model=movie_genre_association, form={"content_id":created_content, "genre_id":genre.genre_id})

        return CreatedResponse()
    
    except (BotoCoreError, ClientError) as e:
        return CustomResponse(status_code=400, detail=str(e))


@content_router.put("/update_content")
async def update_content(
    id: int = Form(description="Content ID", repr=False),
    title: Optional[str] = Form(None, description="Sarlavha", repr=False),
    description: Optional[str] = Form(None, description="Batafsil ma'lumot", repr=False),
    genre: Optional[List[int]] = Form(None, description="Janr", repr=False),
    release_date: Optional[date] = Form(None, description="Chiqarilgan sana", repr=False),
    dubbed_by: Optional[str] = Form(None, description="Dublaj qilingan studio nomi", repr=False),
    status: Optional[ContentStatusEnum] = Form(None, description="Status", repr=False),
    subscription_status: Optional[bool] = Form(None, description="Obunalik kontent", repr=False),
    type: Optional[ContentType] = Form(None, description="Content type", repr=False),
    thumbnail: Optional[UploadFile] = File(None, description="Rasm", repr=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
    ):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")

    get_content = await get_one(db=db, model=Content, filter_query=(Content.content_id==id))
    if not get_content:
        return CustomResponse(status_code=400, detail="Bunday kontent mavjud emas")
    
    if genre:
        get_genre = await get_all(db=db, model=Genre, filter_query=(Genre.genre_id.in_(genre)))
        if len(get_genre['data']) != len(genre):
            return CustomResponse(status_code=400, detail="Bunday janr mavjud emas")


    if release_date:
        if release_date < MIN_DATE:
            return CustomResponse(status_code=400, detail="Sana 1900-yildan past bo'lmasligi kerak")

    form = {}
    if title:
        form["title"] = title
    if description:
        form["description"] = description
    if genre:
        await remove(db=db, model=movie_genre_association, filter_query=and_(movie_genre_association.c.content_id==id))
        for genre_id in get_genre['data']:
            await create(db=db, model=movie_genre_association, form={"content_id":id, "genre_id":genre_id.genre_id})

    if release_date:
        form["release_date"] = release_date
    if dubbed_by:
        form["dubbed_by"] = dubbed_by
    if status:
        form["status"] = status
    if subscription_status is not None:
        form["subscription_status"] = subscription_status
    if type:
        form["type"] = type
    if thumbnail:
        save_thumbnail = await upload_thumbnail_to_r2(thumbnail)
        form["thumbnail"] = save_thumbnail

    await change(db=db, model=Content, filter_query=(Content.content_id==id), form=form)
    return UpdatedResponse()

@content_router.delete("/delete_content")
async def delete_content(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    get_content = await get_one(db=db, model=Content, filter_query=(Content.content_id==id))
    if not get_content:
        return CustomResponse(status_code=400, detail="Bunday kontent mavjud emas")
    
    if current_user.role != "admin" and get_content.uploader_id != current_user.id:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    await remove(db=db, model=Content, filter_query=(Content.content_id==id))
    return DeletedResponse()
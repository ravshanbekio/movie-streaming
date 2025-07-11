from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import ORJSONResponse
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, date
from botocore.exceptions import BotoCoreError, ClientError


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
from utils.compressor import upload_thumbnail_to_r2
from utils.pagination import Page

content_router = APIRouter(tags=["Content"], prefix="/contents")
MIN_DATE = date(1970, 1, 1)

@content_router.get("/all")
async def get_all_contents(page: int = 1, limit: int = 25, status: ContentSchema = None, search: str = None, 
                           db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    filter_query = []
    if status:
        if status == ContentSchema.shows:
            filter_query.append(Content.type==ContentType.show)
        if status == ContentSchema.films:
            filter_query.append(Content.type==ContentType.film)
        if status == ContentSchema.ongoing:
            filter_query.append(Content.status==ContentStatusEnum.ongoing)
        if status == ContentSchema.stopped:
            filter_query.append(Content.status==ContentStatusEnum.stopped)
        if status == ContentSchema.premium:
            filter_query.append(Content.subscription_status==True)

    if search:
        filter_query.append(or_(Content.title.like(f"%{search}%"), Content.description.like(f"%{search}%")))

    filters = and_(*filter_query) if filter_query else None
    data = await get_all(db=db, model=Content, filter_query=filters, options=[joinedload(Content.genre_data), selectinload(Content.episodes)], unique=True, page=page, limit=limit)

    seasions = []
    for content in data['data']:
        content.seasions = list(set(ep.seasion for ep in content.episodes))
        del content.episodes

    result = [ContentResponse.model_validate(content).model_dump() for content in data["data"]]
    return ORJSONResponse({
        "total_pages": data["total_pages"],
        "current_page": data["current_page"],
        "limit": data["limit"],
        "data": result
    })

@content_router.get("/one")
async def get_one_content(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)) -> ContentDetailResponse:
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
    data = await get_one(db=db, model=Content, filter_query=and_(Content.content_id==id, Content.uploader_id==current_user.id), options=[joinedload(Content.genre_data)])
    if not data:
        return CustomResponse(status_code=400, detail="Bunday ma'lumot mavjud emas")
    
    return data
    

@content_router.post("/create_content")
async def create_content(
    title: str = Form(description="Sarlavha", repr=False),
    description: Optional[str] = Form(None, description="Batafsil ma'lumot", repr=False),
    genre: List[int] = Form(None, description="Janr", repr=False),
    release_date: Optional[date] = Form(None, description="Chiqarilgan sana", repr=False),
    dubbed_by: Optional[str] = Form(None, description="Dublaj qilingan studio nomi", repr=False),
    status: ContentStatusEnum = Form(description="Status", repr=False),
    subscription_status: bool = Form(description="Obunalik kontent", repr=False),
    thumbnail: UploadFile = File(description="Rasm", repr=False),
    content: UploadFile = File(description="Content", repr=False),
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
        
    try:
        # Cloudga animeni yuklash
        r2.upload_fileobj(
            Fileobj=content.file,
            Bucket=R2_BUCKET,
            Key=f"contents/{content.filename}",
            ExtraArgs={'ContentType': content.content_type}
        )

        # Cloudga trailerni yuklash (agar bor bo'lsa)
        if trailer:
            r2.upload_fileobj(
            Fileobj=trailer.file,
            Bucket=R2_BUCKET,
            Key=f"trailers/{trailer.filename}",
            ExtraArgs={'ContentType': trailer.content_type}
        )
    
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
            "content_url":f"{R2_PUBLIC_ENDPOINT}/{R2_BUCKET}/contents/{content.filename}",
            "trailer_url":f"{R2_PUBLIC_ENDPOINT}/{R2_BUCKET}/trailers/{trailer.filename}" if trailer else None,
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
    thumbnail: Optional[UploadFile] = File(None, description="Rasm", repr=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
    ):
    if current_user.role not in AdminRole:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")

    get_content = await get_one(db=db, model=Content, filter_query=(Content.content_id==id))
    if not get_content:
        return CustomResponse(status_code=400, detail="Bunday kontent mavjud emas")
    
    if current_user.role != "admin" and get_content.uploader_id != current_user.id:
        return CustomResponse(status_code=400, detail="Sizda yetarli huquqlar yo'q")
    
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
    if thumbnail:
        save_thumbnail = await upload_thumbnail_to_r2(thumbnail)
        form['thumbnail'] = save_thumbnail

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
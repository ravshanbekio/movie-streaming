import uuid
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from crud import change

async def save_image(folder: str, file: UploadFile):
    UPLOAD_DIR = Path(f"static/{folder}")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}_{file.filename}"

    file_path = UPLOAD_DIR / filename

    if file and file.content_type not in ['image/png', 'image/jpg', 'image/jpeg', 'image/svg', 'images/webp']:
        raise HTTPException(
            status_code=400,
            detail="Banner uchun quydagi formatlarga ruxsat berilgan: *.png, .*jpg, *.jpeg, *.svg, *.webp"
        )

    # Save the file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {"filename": filename, "path": str(file_path)}


async def save_content(folder: str, db: AsyncSession, model, filter_query: tuple, content: UploadFile, trailer: UploadFile = None):
    print("JARAYON BOSHLANDI")
    UPLOAD_DIR = Path(f"static/{folder}")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    content_path = UPLOAD_DIR / content.filename

    if content and content.content_type not in ['video/mp4', 'video/x-msvideo', 'video/x-matroska', 'video/webm', 'video/mpeg',
                                          'video/3gpp']:
        raise HTTPException(
            status_code=400,
            detail="Media fayl uchun quydagi formatlarga ruxsat berilgan: *.mp4, .*avi, *.mkv, *.webm, *.mpeg, *.3gpp"
        )
    
    trailer_path = None
    if trailer:
        trailer_path = UPLOAD_DIR / trailer.filename

        if trailer and trailer.content_type not in ['video/mp4', 'video/x-msvideo', 'video/x-matroska', 'video/webm', 'video/mpeg',
                                          'video/3gpp']:
            raise HTTPException(
                status_code=400,
                detail="Trailer uchun quydagi formatlarga ruxsat berilgan: *.mp4, .*avi, *.mkv, *.webm, *.mpeg, *.3gpp"
            )
        # Save the trailer
        with open(trailer_path, "wb") as buffer:
            trailer = await trailer.read()
            buffer.write(trailer)

    # Save the content
    with open(content_path, "wb") as buffer:
        content = await content.read()
        buffer.write(content)

    form = {
        "content_url":str(content_path),
        "trailer_url":str(trailer_path)
    }

    await change(db=db, model=model, filter_query=filter_query, form=form)
    print("JARAYON TO'LIQ YAKUNLANDI")
    return {"content_path": str(content_path), "trailer_path":str(trailer_path)}
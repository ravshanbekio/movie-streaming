import uuid
from fastapi import HTTPException, UploadFile
from pathlib import Path

MAX_IMAGE_SIZE = 5242880
MAX_CONTENT_SIZE = 2621440000

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
    
    if file.size > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Banner uchun rasm 5MB dan oshmasligi kerak")

    # Save the file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {"filename": filename, "path": str(file_path)}


async def save_content(folder: str, file: UploadFile):
    UPLOAD_DIR = Path(f"static/{folder}")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}_{file.filename}"

    file_path = UPLOAD_DIR / filename

    if file and file.content_type not in ['video/mp4', 'video/x-msvideo', 'video/x-matroska', 'video/webm', 'video/mpeg',
                                          'video/3gpp']:
        raise HTTPException(
            status_code=400,
            detail="Media fayl uchun quydagi formatlarga ruxsat berilgan: *.mp4, .*avi, *.mkv, *.webm, *.mpeg, *.3gpp"
        )
    
    if file.size > MAX_CONTENT_SIZE:
        raise HTTPException(status_code=400, detail="Media fayl uchun rasm 2.5GB dan oshmasligi kerak")

    # Save the file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {"filename": filename, "path": str(file_path)}
import uuid
from fastapi import HTTPException, UploadFile
from pathlib import Path

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
    
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Banner uchun rasm 5MB dan oshmasligi kerak")

    # Save the file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {"filename": filename, "path": str(file_path)}

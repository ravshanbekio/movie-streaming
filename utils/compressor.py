import uuid
from fastapi import UploadFile
from io import BytesIO
import os
import asyncio
import shutil
from pathlib import Path

from .r2_utils import r2, R2_BUCKET, R2_PUBLIC_ENDPOINT

AVAILABLE_VIDEO_FORMATS = [
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo", 
    "video/x-ms-wmv",     
    "video/x-matroska",    
    "video/webm",          
    "video/x-flv" 
]
AVAILABLE_IMAGE_FORMATS = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp", 
    "image/svg+xml", 
    "image/tiff"
]

async def upload_thumbnail_to_r2(thumbnail: UploadFile) -> str:
    # Create unique object key
    extension = thumbnail.filename.split(".")[-1]
    object_key = f"thumbnails/{uuid.uuid4().hex}.{extension}"

    # Read file content
    data = await thumbnail.read()

    image_stream = BytesIO(data)

    # Upload to R2
    r2.put_object(
        Bucket=R2_BUCKET,
        Key=object_key,
        Body=image_stream,
        ContentType=thumbnail.content_type or "image/jpeg"
    )

    # Return public URL
    return f"{R2_PUBLIC_ENDPOINT}/{object_key}"
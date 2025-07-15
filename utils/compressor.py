import uuid
from fastapi import UploadFile
from io import BytesIO
import os
import subprocess

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

async def convert_from_url_to_r2(input_url, filename, output_prefix):
    os.makedirs("/tmp/hls", exist_ok=True)

    # ffmpeg command to read from input_url and write to HLS
    cmd = [
        "ffmpeg", "-i", input_url,
        "-preset", "fast", "-g", "48", "-sc_threshold", "0",
        "-map", "0:0", "-map", "0:1?",
        "-b:v", "3000k", "-b:a", "128k",
        "-hls_time", "6", "-hls_playlist_type", "vod",
        "-hls_segment_filename", "/tmp/hls/seg_%03d.ts",
        "/tmp/hls/master.m3u8"
    ]

    subprocess.run(cmd, check=True)

    # Upload output to R2
    for fname in os.listdir("/tmp/hls"):
        key = f"{output_prefix}/{filename}/{fname}"
        with open(f"/tmp/hls/{fname}", "rb") as f:
            r2.upload_fileobj(f, R2_BUCKET, key)

    return True
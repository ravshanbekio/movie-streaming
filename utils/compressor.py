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


ffmpeg_semaphore = asyncio.Semaphore(1)  # tune to 2 or more if RAM allows

async def convert_from_url_to_r2(input_url: str, filename: str, output_prefix: str):
    temp_dir = Path("/tmp/hls")
    temp_dir.mkdir(parents=True, exist_ok=True)

    output_path = temp_dir / "master.m3u8"
    segment_path = str(temp_dir / "seg_%03d.ts")

    cmd = [
        "ffmpeg", "-i", input_url,
        "-preset", "fast", "-g", "48", "-sc_threshold", "0",
        "-map", "0:0", "-map", "0:1?",
        "-b:v", "3000k", "-b:a", "128k",
        "-hls_time", "6", "-hls_playlist_type", "vod",
        "-hls_segment_filename", segment_path,
        str(output_path)
    ]

    try:
        async with ffmpeg_semaphore:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                raise RuntimeError(f"FFMPEG failed: {error_msg}")

        # Upload output to R2
        for fname in os.listdir(temp_dir):
            file_path = temp_dir / fname
            key = f"{output_prefix}/{filename}/{fname}"
            with open(file_path, "rb") as f:
                r2.upload_fileobj(f, R2_BUCKET, key)

        return True

    except Exception as e:
        return str(e)

    finally:
        # Clean up temp files to save disk space
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        
def hello_task():
    print("✅ This is a test job!", flush=True)
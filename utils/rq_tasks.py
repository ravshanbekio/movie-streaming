import logging
import sys
import asyncio
import os
import subprocess
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from utils.r2_utils import r2, R2_BUCKET

from crud import change
from models.episode import Episode
from models.content import Content

logger = logging.getLogger("rq.video")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

ffmpeg_semaphore = asyncio.Semaphore(2)

def rq_convert_and_upload(
    db,
    id,
    input_url: str,
    filename: str,
    output_prefix: str
):
    """
    RQ ENTRY POINT (SYNC)
    """
    logger.info("[RQ Task] Wrapper started")
    asyncio.run(
        convert_and_upload(
            db=db,
            id=id,
            input_url=input_url,
            filename=filename,
            output_prefix=output_prefix
        )
    )

async def convert_and_upload(
        db,
        id,
        input_url: str, 
        filename: str, 
        output_prefix: str
                        ):
    logger.info("[RQ Task] Started", )
    await _convert_and_upload_async(input_url, filename, output_prefix)
    if output_prefix == "episodes":
        model = Episode
        filter_query = Episode.id==id
        form = {
            "converted_episode": f"{input_url}/"
        }
    elif output_prefix == "contents":
        model = Content
        filter_query = Content.content_id==id
        form = {
            "converted_content":f"{input_url}/"
        }
    elif output_prefix == "trailers":
        model = Content
        filter_query = Content.content_id==id
        form = {
            "converted_trailer":f"{input_url}/"
        }
    
    #  Create Async DB Session
    engine = create_async_engine(db, echo=False, future=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        await change(db=session, model=model, filter_query=filter_query, form=form)

def _get_source_resolution_wh(input_url: str) -> tuple[int, int]:
    """Uses ffprobe to get the source video's width and height."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json", input_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        
        if "streams" in info and len(info["streams"]) > 0:
            stream = info["streams"][0]
            width = stream.get("width")
            height = stream.get("height")
            if width is not None and height is not None:
                return int(width), int(height)
                
    except (subprocess.CalledProcessError, json.JSONDecodeError, Exception) as e:
        logger.info(f"[ERROR] Failed to get source resolution for {input_url}: {e}")
        return 0, 0
    
    return 0, 0

async def _convert_and_upload_async(input_url: str, filename: str, output_prefix: str):
    logger.info("[RQ Task] Async started (Original Resolution Only)", )
    temp_dir = Path(f"/tmp/{output_prefix}/hls/{filename}/")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 💡 Lokal serverda vaqtinchalik fayl yo'li
    local_source_path = Path(f"/tmp/raw_source_{filename}")

    try:
        # 💡 0. Videoni FFmpeg ishlatishdan oldin serverga yuklab olish
        # Bu tarmoqdagi uzilishlar konvertatsiyani to'xtatib qo'ymasligini ta'minlaydi
        logger.info(f"[RQ Task] Original videoni R2 dan yuklab olish boshlandi: {filename}")
        r2.download_file(R2_BUCKET, f"{output_prefix}/{filename}", str(local_source_path))
        logger.info("[RQ Task] Original video lokalga muvaffaqiyatli yuklandi.")

        # 💡 1. Asl o'lchamni olish (Endi lokal fayldan o'qiymiz)
        source_width, source_height = _get_source_resolution_wh(str(local_source_path))
        if source_height == 0:
            raise RuntimeError("Asl video o'lchamini aniqlab bo'lmadi.")
            
        resolution_str = f"{source_width}x{source_height}"
        rendition_name = f"original_{source_height}p"

        logger.info(f"[RQ Task] Asl video o'lchami: {resolution_str}. Faqat shu o'lchamda konvertatsiya qilinadi.", )

        # 💡 2. Yagona konvertatsiya uchun ma'lumotlarni tayyorlash
        original_rendition = {
            "name": rendition_name,
            "resolution": resolution_str,
            "bitrate": "8000k", 
            "maxrate": "8560k",
            "bufsize": "12000k",
        }

        # 💡 3. Konvertatsiya qilish
        async def convert_original(r):
            async with ffmpeg_semaphore:
                subdir = temp_dir / r["name"]
                subdir.mkdir(parents=True, exist_ok=True)
                segment_path = str(subdir / "seg_%03d.ts")
                output_path = subdir / "playlist.m3u8"
                
                cmd = [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", str(local_source_path), # 💡 URL o'rniga lokal fayl berildi
                    "-vf", f"scale={r['resolution']}", 
                    "-c:a", "aac", "-ar", "48000",
                    "-c:v", "h264", "-profile:v", "main", "-crf", "20", "-sc_threshold", "0",
                    "-preset", "ultrafast",
                    "-vsync", "2",
                    "-b:v", r["bitrate"],
                    "-maxrate", r["maxrate"],
                    "-bufsize", r["bufsize"],
                    "-hls_flags", "independent_segments",
                    "-hls_time", "6", "-hls_playlist_type", "vod",
                    "-hls_segment_filename", segment_path,
                    str(output_path)
                ]
                
                logger.info(
                    "[RQ Task] Executing FFMPEG for original stream: %s",
                    " ".join(cmd),
                )
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                logger.info(f"[RQ Task] ffmpeg started for original stream")
                try:
                    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=14400)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    raise RuntimeError("FFmpeg vaqti tugadi (Timeout)")

                if proc.returncode != 0:
                    error_msg = stderr.decode().strip()
                    raise RuntimeError(f"FFmpeg xato qildi: {error_msg}")

        # Yagona konvertatsiyani bajarish
        await convert_original(original_rendition)

        master_path = temp_dir / "master.m3u8"
        bw = original_rendition['bitrate'].replace("k", "000")
        
        master_playlist = "#EXTM3U\n#EXT-X-VERSION:3\n"
        master_playlist += f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={resolution_str}\n{original_rendition['name']}/playlist.m3u8\n"

        with open(master_path, "w") as f:
            f.write(master_playlist)
        logger.info("[RQ Task] Master playlist yaratildi.")

        logger.info("[RQ Task] Barcha segmentlar va playlistlar yuklanmoqda...")
        for root, _, files in os.walk(temp_dir):
            for fname in files:
                file_path = Path(root) / fname
                relative_path = file_path.relative_to(temp_dir)
                key = f"{output_prefix}/{filename}/{relative_path}".replace("\\", "/")
                with open(file_path, "rb") as f:
                    r2.upload_fileobj(f, R2_BUCKET, key)
                    logger.info(f"[RQ Task] Yuklandi: {key}")

        logger.info("[RQ Task] ✅ Barcha fayllar muvaffaqiyatli yuklandi", )

    except Exception as e:
        logger.info(f"[RQ Task] ❌ Xato: {str(e)}")

    finally:
        # 💡 Tozalash: ham temp_dir, ham yuklab olingan original faylni o'chirish
        shutil.rmtree(temp_dir, ignore_errors=True)
        if local_source_path.exists():
            local_source_path.unlink()
        logger.info("[RQ Task] Vaqtinchalik katalog va lokal video tozalandi", )
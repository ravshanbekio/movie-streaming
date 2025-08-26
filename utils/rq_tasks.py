import asyncio
import os
import shutil
from pathlib import Path
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from utils.r2_utils import r2, R2_BUCKET

from crud import change
from models.episode import Episode
from models.content import Content

# Assume you have this globally if you used it before
ffmpeg_semaphore = asyncio.Semaphore(2)

async def convert_and_upload(
        db,
        id,
        input_url: str, 
        filename: str, 
        output_prefix: str
                        ):
    print("[RQ Task] Started", flush=True)
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

async def _convert_and_upload_async(input_url: str, filename: str, output_prefix: str):
    print("[RQ Task] Async started", flush=True)
    temp_dir = Path("/tmp/hls")
    temp_dir.mkdir(parents=True, exist_ok=True)

    renditions = [
        {"name": "360p",  "resolution": "640x360",   "bitrate": "800k",  "maxrate": "856k",  "bufsize": "1200k"},
        {"name": "480p",  "resolution": "854x480",   "bitrate": "1400k", "maxrate": "1498k", "bufsize": "2100k"},
        {"name": "720p",  "resolution": "1280x720",  "bitrate": "2800k", "maxrate": "2996k", "bufsize": "4200k"},
        {"name": "1080p", "resolution": "1920x1080", "bitrate": "5000k", "maxrate": "5350k", "bufsize": "7500k"},
    ]

    try:
        async def convert_rendition(r):
            async with ffmpeg_semaphore:
                subdir = temp_dir / r["name"]
                subdir.mkdir(parents=True, exist_ok=True)
                segment_path = str(subdir / "seg_%03d.ts")
                output_path = subdir / "playlist.m3u8"

                cmd = [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", input_url,
                    "-vf", f"scale={r['resolution']}",
                    "-c:a", "aac", "-ar", "48000",
                    "-c:v", "h264", "-profile:v", "main", "-crf", "20", "-sc_threshold", "0",
                    "-preset", "ultrafast",
                    "-g", "48", "-keyint_min", "48",
                    "-b:v", r["bitrate"],
                    "-maxrate", r["maxrate"],
                    "-bufsize", r["bufsize"],
                    "-hls_time", "6", "-hls_playlist_type", "vod",
                    "-hls_segment_filename", segment_path,
                    str(output_path)
                ]

                print(f"[RQ Task] Executing FFMPEG for {r['name']}:", " ".join(cmd), flush=True)
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                print(f"[RQ Task] ffmpeg started for {r['name']}", flush=True)
                try:
                    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=5000)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    raise RuntimeError("FFmpeg timed out")

                if proc.returncode != 0:
                    error_msg = stderr.decode().strip()
                    raise RuntimeError(f"FFmpeg failed for {r['name']}: {error_msg}")

        # ✅ Run all renditions in parallel (with max 2 at once)
        await asyncio.gather(*[convert_rendition(r) for r in renditions])

        # Write master.m3u8
        master_path = temp_dir / "master.m3u8"
        master_playlist = "#EXTM3U\n#EXT-X-VERSION:3\n"
        for r in renditions:
            bw = r['bitrate'].replace("k", "000")
            master_playlist += f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={r['resolution']}\n{r['name']}/playlist.m3u8\n"

        with open(master_path, "w") as f:
            f.write(master_playlist)

        print("[RQ Task] Uploading all segments...", flush=True)
        for root, _, files in os.walk(temp_dir):
            for fname in files:
                file_path = Path(root) / fname
                relative_path = file_path.relative_to(temp_dir)
                key = f"{output_prefix}/{filename}/{relative_path}".replace("\\", "/")
                with open(file_path, "rb") as f:
                    r2.upload_fileobj(f, R2_BUCKET, key)
                    print(f"[RQ Task] Uploaded: {key}", flush=True)

        print("[RQ Task] ✅ All renditions uploaded", flush=True)

    except Exception as e:
        print("[RQ Task] ❌ Exception:", str(e), flush=True)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("[RQ Task] Cleaned up temp dir", flush=True)

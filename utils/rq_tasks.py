import asyncio
import os
import shutil
from pathlib import Path
from utils.r2_utils import r2, R2_BUCKET

# Assume you have this globally if you used it before
ffmpeg_semaphore = asyncio.Semaphore(2)

def convert_and_upload(input_url: str, filename: str, output_prefix: str):
    print("[RQ Task] Started", flush=True)
    asyncio.run(_convert_and_upload_async(input_url, filename, output_prefix))

async def _convert_and_upload_async(input_url: str, filename: str, output_prefix: str):
    print("[RQ Task] Async started", flush=True)
    temp_dir = Path("/tmp/hls")
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / "master.m3u8"
    segment_path = str(temp_dir / "seg_%03d.ts")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", input_url,
        "-preset", "fast", "-g", "48", "-sc_threshold", "0",
        "-map", "0:0", "-b:v", "3000k",
        "-hls_time", "6", "-hls_playlist_type", "vod",
        "-hls_segment_filename", segment_path,
        str(output_path)
    ]

    try:
        print("[RQ Task] Executing:", " ".join(cmd), flush=True)

        async with ffmpeg_semaphore:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip()
            print("[RQ Task] FFMPEG failed:", error_msg, flush=True)
            return

        print("[RQ Task] Uploading segments...", flush=True)
        for fname in os.listdir(temp_dir):
            file_path = temp_dir / fname
            key = f"{output_prefix}/{filename}/{fname}"
            with open(file_path, "rb") as f:
                r2.upload_fileobj(f, R2_BUCKET, key)
                print(f"[RQ Task] Uploaded: {key}", flush=True)

        print("[RQ Task] ✅ HLS conversion and upload complete", flush=True)

    except Exception as e:
        print("[RQ Task] ❌ Exception:", str(e), flush=True)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("[RQ Task] Cleaned up temp dir", flush=True)

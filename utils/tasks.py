import asyncio

from crud import change
from utils.r2_utils import check_file_exists_in_r2

async def verify_upload_background(db, model, filter_query, content_object_key: str, trailer_object_key: str = None):
    try:
        print("[Background Task] Starting to check R2 upload status...")
        # Wait up to 60 seconds (check every 5 sec)
        for _ in range(12):
            if check_file_exists_in_r2(content_object_key, trailer_object_key):
                await change(db=db, model=model, filter_query=filter_query, form={"is_processing":False})
                print("[Background Task] Upload complete ✅")
                return
            await asyncio.sleep(60)

        print("[Background Task] Upload timed out or failed ❌")

    except Exception as e:
        print(f"[Background Task Error] {e}")

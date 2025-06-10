from pydantic import BaseModel
from typing import Optional
from datetime import date

class PlaylistResponse(BaseModel):
    playlist_id: int
    title: str
    description: Optional[str]
    thumbnail: str
    created_at: Optional[date]
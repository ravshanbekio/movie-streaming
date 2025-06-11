from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from .content import ContentResponse

class PlaylistResponse(BaseModel):
    playlist_id: int
    title: str
    description: Optional[str]
    thumbnail: str
    created_at: Optional[date]

class PlaylistDetailResponse(PlaylistResponse):
    contents: List[ContentResponse]
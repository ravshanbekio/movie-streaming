from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from .genre import GenreResponse
from .episode import EpisodeSeasionResponse

class ContentResponse(BaseModel):
    content_id: int
    title: str
    description: Optional[str]
    release_date: Optional[date]
    dubbed_by: Optional[str]
    status: str
    subscription_status: bool
    thumbnail: str

    seasions: Optional[List[str]] = []

    class Config:
        from_attributes = True

class ContentGenreResponse(ContentResponse):
    genre_data: GenreResponse
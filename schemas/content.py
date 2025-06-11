from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

from .genre import GenreResponse

class ContentResponse(BaseModel):
    content_id: int
    title: str
    description: Optional[str]
    quality: Optional[str]
    release_date: Optional[date]
    dubbed_by: Optional[str]
    thumbnail: str
    content_url: str
    created_at: datetime

class ContentGenreResponse(ContentResponse):
    genre_data: GenreResponse
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

    genre_data: List[GenreResponse]
    seasions: Optional[List[str]] = []

    class Config:
        from_attributes = True

class ContentDetailResponse(BaseModel):
    content_id: int
    title: str
    description: Optional[str]
    release_date: Optional[date]
    dubbed_by: Optional[str]
    status: str
    subscription_status: bool
    thumbnail: str

    genre_data: List[GenreResponse]

    class Config:
        orm_mode = True
        from_attributes = True
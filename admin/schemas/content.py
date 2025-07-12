from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from .genre import GenreResponse
from .episode import EpisodeSeasionResponse

class ContentSchema(str, Enum):
    shows = "shows"
    films = "films"
    ongoing = "ongoing"
    stopped = "stopped"
    premium = "premium"

class ContentType(str, Enum):
    show = "show"
    film = "film"

class ContentStatusEnum(str, Enum):
    ongoing = "davom etayotgan"
    stopped = "tugatilgan"

class ContentResponse(BaseModel):
    content_id: int
    title: str
    description: Optional[str]
    release_date: Optional[date]
    dubbed_by: Optional[str]
    status: ContentStatusEnum
    subscription_status: bool
    content_duration: Optional[str]
    trailer_duration: Optional[str]
    thumbnail: str
    type: ContentType

    genre_data: List[GenreResponse]

    class Config:
        from_attributes = True

class ContentDetailResponse(BaseModel):
    content_id: int
    title: str
    description: Optional[str]
    release_date: Optional[date]
    dubbed_by: Optional[str]
    status: ContentStatusEnum
    subscription_status: bool
    thumbnail: str
    type: ContentType

    genre_data: List[GenreResponse]

    class Config:
        orm_mode = True
        from_attributes = True
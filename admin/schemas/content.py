from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from .genre import GenreResponse
from .episode import EpisodeSeasionResponse

class ContentSchema(str, Enum):
    ongoing = "ongoing"
    stopped = "stopped"

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
    original_content: Optional[str]
    converted_content: Optional[str]
    original_trailer: Optional[str]
    converted_trailer: Optional[str]
    thumbnail: str
    content_duration: Optional[str]
    trailer_duration: Optional[str]
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
    original_content: Optional[str]
    converted_content: Optional[str]
    original_trailer: Optional[str]
    converted_trailer: Optional[str]
    thumbnail: str
    status: ContentStatusEnum
    subscription_status: bool
    type: ContentType

    genre_data: List[GenreResponse]

    class Config:
        orm_mode = True
        from_attributes = True
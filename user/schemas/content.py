from pydantic import BaseModel
from typing import Optional, List
from datetime import date

from admin.schemas.content import ContentType
from .episode import EpisodeResponse

class ContentResponse(BaseModel):
    content_id: int
    title: str
    description: Optional[str]
    type: ContentType
    
    
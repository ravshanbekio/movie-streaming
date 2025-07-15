from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from .content import ContentResponse
from .episode import EpisodeResponse

class UserSavedResponse(BaseModel):
    id: int
    
    content: ContentResponse
    episode: Optional[EpisodeResponse]

class UserSavedForm(BaseModel):
    content_id: int
    episode_id: Optional[int] = None
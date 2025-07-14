from pydantic import BaseModel
from typing import Optional

from .content import ContentResponse
from .episode import EpisodeResponse

class HistoryResponse(BaseModel):
    id: int
    duration: str
    
    content: ContentResponse
    episode: EpisodeResponse

class HistoryForm(BaseModel):
    content_id: int
    episode_id: Optional[int]
    duration: str
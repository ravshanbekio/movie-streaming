from pydantic import BaseModel
from typing import Optional

class EpisodeResponse(BaseModel):
    id: int
    content_id: int
    seasion: str
    episode: str
    episode_video: str
    episode_thumbnail: str
    duration: int
    
    class Config:
        from_attributes = True

class EpisodeSeasionResponse(BaseModel):
    seasion: str

    class Config:
        from_attributes = True
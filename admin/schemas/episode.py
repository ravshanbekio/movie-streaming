from pydantic import BaseModel
from typing import Optional

class EpisodeResponse(BaseModel):
    id: int
    content_id: int
    seasion: int
    episode: int
    episode_video: str
    episode_thumbnail: str
    duration: str
    
    class Config:
        from_attributes = True

class EpisodeSeasionResponse(BaseModel):
    seasion: str

    class Config:
        from_attributes = True
from pydantic import BaseModel
from typing import Optional

class EpisodeResponse(BaseModel):
    id: int
    seasion: int
    episode: int
    episode_video: str
    episode_thumbnail: str
    duration: str
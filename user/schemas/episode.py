from pydantic import BaseModel
from typing import Optional

class EpisodeResponse(BaseModel):
    id: int
    seasion: int
    episode: int
    original_episode: str
    converted_episode: Optional[str]
    episode_thumbnail: str
    duration: str
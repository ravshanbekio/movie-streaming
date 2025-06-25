from pydantic import BaseModel
from typing import Optional

class GenreResponse(BaseModel):
    genre_id: int
    title: str

    class Config:
        from_attributes = True

class GenreCreateForm(BaseModel):
    title: str

class GenreUpdateForm(BaseModel):
    genre_id: int
    title: Optional[str]
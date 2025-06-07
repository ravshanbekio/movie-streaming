from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, List

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    total_pages: int
    current_page: int
    limit: int
    data: List[T]

async def paginate(data: list, total: int, page: int, limit: int):
    total_pages = (total + limit - 1) // limit
    return {
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit,
        "data": data
    }
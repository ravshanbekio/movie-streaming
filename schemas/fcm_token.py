from pydantic import BaseModel

class TokenCreate(BaseModel):
    user_id: int
    token: str
    
class BroadcastForm(BaseModel):
    title: str
    body: str
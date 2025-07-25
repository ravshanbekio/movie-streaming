from pydantic import BaseModel, Field

class CreatePlanForm(BaseModel):
    title: str
    description: str
    price: float = Field(ge=1)
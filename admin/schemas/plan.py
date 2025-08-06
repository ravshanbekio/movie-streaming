from pydantic import BaseModel, Field

class CreatePlanForm(BaseModel):
    month: int = Field(ge=1)
    price: float = Field(ge=1)
from pydantic import BaseModel
from datetime import datetime

class ApplicationCreate(BaseModel):
    user_name: str
    description: str

class ApplicationResponse(ApplicationCreate):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True
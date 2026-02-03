from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from core.models import TaskStatus

class TaskRead(BaseModel):
    id: int
    description: str
    status: TaskStatus
    created_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

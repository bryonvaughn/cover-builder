from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    author: str
    genre: str
    subgenre: Optional[str] = None


class ProjectOut(BaseModel):
    id: UUID
    title: str
    author: str
    genre: str
    subgenre: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

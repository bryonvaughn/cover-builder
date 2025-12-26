from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class CoverImageGenerateRequest(BaseModel):
    project_id: UUID
    brief_run_id: Optional[UUID] = None
    direction_index: Optional[int] = Field(default=None, ge=0, le=20)

    prompt: str
    n: int = Field(default=1, ge=1, le=4)

    # optional overrides; otherwise backend defaults
    model: Optional[str] = None
    size: Optional[str] = None

class CoverImageOut(BaseModel):
    id: UUID
    project_id: UUID
    brief_run_id: Optional[UUID]
    direction_index: Optional[int]

    prompt: str
    model: str
    size: str

    image_url: str

class CoverImageGenerateResponse(BaseModel):
    images: list[CoverImageOut]

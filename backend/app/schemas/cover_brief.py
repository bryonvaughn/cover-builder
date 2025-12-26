from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

class CoverBriefRequest(BaseModel):
    project_id: UUID

    title: str
    subtitle: Optional[str] = None
    author: str

    genre: str
    subgenre: Optional[str] = None
    blurb: Optional[str] = None

    tone_words: List[str] = Field(default_factory=list)
    comps: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

class CoverDirection(BaseModel):
    name: str
    one_liner: str
    imagery: str
    typography: str
    color_palette: str
    layout_notes: str
    avoid: str
    image_prompt: str

class CoverBriefResponse(BaseModel):
    directions: List[CoverDirection]
    model: str

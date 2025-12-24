from pydantic import BaseModel, Field
from typing import List, Optional


class CoverBriefRequest(BaseModel):
    title: str
    subtitle: Optional[str] = None
    author: str

    genre: str = Field(..., description="Primary genre (e.g., Romance, Thriller, Memoir)")
    subgenre: Optional[str] = Field(None, description="More specific subgenre (e.g., Rock Star Romance)")
    blurb: Optional[str] = None

    tone_words: List[str] = Field(default_factory=list, description="Mood / tone keywords")
    comps: List[str] = Field(default_factory=list, description="Comparable titles/authors")
    constraints: List[str] = Field(default_factory=list, description="Hard constraints to respect")


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

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class BriefRunOut(BaseModel):
    id: UUID
    project_id: UUID
    model: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    request_json: dict[str, Any]
    response_json: dict[str, Any]

    class Config:
        from_attributes = True

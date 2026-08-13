import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.content_visibility import ContentVisibility


class ReelCreate(BaseModel):
    url: str
    caption: str | None = None
    visibility: ContentVisibility = ContentVisibility.PUBLIC


class ReelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_profile_id: uuid.UUID
    platform: str
    url: str
    caption: str | None
    visibility: ContentVisibility
    created_at: datetime

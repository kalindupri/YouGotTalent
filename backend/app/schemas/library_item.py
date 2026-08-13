import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.content_visibility import ContentVisibility


class LibraryItemCreate(BaseModel):
    title: str
    description: str | None = None
    media_type: str
    url: str
    visibility: ContentVisibility = ContentVisibility.PUBLIC


class LibraryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_id: uuid.UUID
    title: str
    description: str | None
    media_type: str
    url: str
    visibility: ContentVisibility
    created_at: datetime

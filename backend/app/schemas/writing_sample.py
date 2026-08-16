import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.content_visibility import ContentVisibility
from app.models.writing_sample import DEFAULT_VISIBLE_LINES


class WritingSampleCreate(BaseModel):
    title: str
    writing_type: str
    language: str
    body: str
    visible_lines: int = Field(default=DEFAULT_VISIBLE_LINES, ge=1)
    visibility: ContentVisibility = ContentVisibility.PUBLIC
    is_published: bool = False


class WritingSampleUpdate(BaseModel):
    title: str | None = None
    writing_type: str | None = None
    language: str | None = None
    body: str | None = None
    visible_lines: int | None = Field(default=None, ge=1)
    visibility: ContentVisibility | None = None
    is_published: bool | None = None


class WritingSampleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_profile_id: uuid.UUID
    title: str
    writing_type: str
    language: str
    body: str
    visible_lines: int
    is_published: bool
    visibility: ContentVisibility
    created_at: datetime
    updated_at: datetime
    # Not a stored column -- set by the route when `body` above has been truncated to
    # `visible_lines` for a non-owner viewer, so the frontend can show a "sample only" hint
    # instead of the reader mistaking the excerpt for the whole piece.
    is_excerpt: bool = False

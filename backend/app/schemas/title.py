import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.title import WorkType


class TitleCreate(BaseModel):
    name: str
    work_type: WorkType
    release_year: int | None = None
    genre: str | None = None
    language: str | None = None
    synopsis: str | None = None
    poster_url: str | None = None


class TitleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    work_type: WorkType
    release_year: int | None
    genre: str | None
    language: str | None
    synopsis: str | None
    poster_url: str | None
    added_by_user_id: uuid.UUID
    created_at: datetime
    average_rating: float | None
    review_count: int


class TitleReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str | None = None


class TitleReviewRead(BaseModel):
    id: uuid.UUID
    rating: int
    body: str | None
    created_at: datetime
    updated_at: datetime
    author_name: str
    author_role: str
    author_profile_id: str | None

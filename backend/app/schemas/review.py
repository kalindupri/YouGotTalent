import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    talent_id: uuid.UUID
    recruiter_id: uuid.UUID
    reviewer_role: str
    rating: int
    comment: str | None
    created_at: datetime
    reviewer_name: str


class TalentReviewSummary(BaseModel):
    average_rating: float | None
    review_count: int
    reviews: list[ReviewRead]


class RecruiterReviewSummary(BaseModel):
    average_rating: float | None
    review_count: int
    reviews: list[ReviewRead]

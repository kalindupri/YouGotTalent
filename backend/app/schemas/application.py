import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    role_id: uuid.UUID
    message: str | None = None
    submission_url: str | None = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    casting_call_id: uuid.UUID
    role_id: uuid.UUID
    talent_id: uuid.UUID
    message: str | None
    submission_url: str | None
    status: ApplicationStatus
    applied_at: datetime
    viewed_at: datetime | None
    match_score: int | None
    pending_offer_status: str | None = None
    talent_display_name: str

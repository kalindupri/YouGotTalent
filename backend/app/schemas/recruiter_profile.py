import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecruiterProfileCreate(BaseModel):
    company_name: str
    industry: str | None = None


class RecruiterProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    industry: str | None
    is_verified: bool
    verification_requested_at: datetime | None
    tier: str
    created_at: datetime

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class RecruiterProfileCreate(BaseModel):
    company_name: str
    recruiter_type: Literal["individual", "agency"] = "agency"
    industry: str | None = None


class RecruiterProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str
    recruiter_type: str
    industry: str | None
    is_verified: bool
    verification_requested_at: datetime | None
    tier: str
    created_at: datetime

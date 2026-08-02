import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreditCreate(BaseModel):
    project_type: str
    title: str
    role: str | None = None
    company_or_director: str | None = None
    location: str | None = None
    date_label: str | None = None
    reference_url: str | None = None


class CreditUpdate(BaseModel):
    project_type: str | None = None
    title: str | None = None
    role: str | None = None
    company_or_director: str | None = None
    location: str | None = None
    date_label: str | None = None
    reference_url: str | None = None


class CreditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_profile_id: uuid.UUID
    project_type: str
    title: str
    role: str | None
    company_or_director: str | None
    location: str | None
    date_label: str | None
    reference_url: str | None
    created_at: datetime

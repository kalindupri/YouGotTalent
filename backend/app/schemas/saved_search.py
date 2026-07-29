import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.talent_profile import TalentCategory


class SavedSearchCreate(BaseModel):
    name: str
    category: TalentCategory | None = None
    city: str | None = None
    q: str | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    verified_only: bool = False


class SavedSearchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recruiter_id: uuid.UUID
    name: str
    category: TalentCategory | None
    city: str | None
    q: str | None
    experience_min: int | None
    experience_max: int | None
    verified_only: bool
    created_at: datetime

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.casting_call import CastingCallStatus
from app.models.talent_profile import TalentCategory
from app.schemas.casting_call_role import CastingCallRoleCreate, CastingCallRoleRead


class CastingCallCreate(BaseModel):
    title: str
    description: str
    category: TalentCategory
    location: str | None = None
    compensation: str | None = None
    application_deadline: date | None = None
    audition_brief: str | None = None
    audition_reference_url: str | None = None
    tags: list[str] | None = None
    shoot_details: str | None = None
    # A job post always has at least one applicable role/stream — for the common single-role
    # case, the frontend just submits one row.
    roles: list[CastingCallRoleCreate] = Field(min_length=1)


class CastingCallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recruiter_id: uuid.UUID
    title: str
    description: str
    category: TalentCategory
    location: str | None
    compensation: str | None
    application_deadline: date | None
    status: CastingCallStatus
    audition_brief: str | None
    audition_reference_url: str | None
    tags: list[str] | None
    shoot_details: str | None
    is_featured: bool
    view_count: int
    created_at: datetime
    roles: list[CastingCallRoleRead] = []

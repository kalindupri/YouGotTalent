import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TalentListCreate(BaseModel):
    name: str


class TalentListMemberCreate(BaseModel):
    talent_id: uuid.UUID
    notes: str | None = None


class TalentListMemberNotesUpdate(BaseModel):
    notes: str | None = None


class TalentListMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_id: uuid.UUID
    notes: str | None
    created_at: datetime
    talent_display_name: str


class TalentListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recruiter_id: uuid.UUID
    name: str
    created_at: datetime
    members: list[TalentListMemberRead] = []

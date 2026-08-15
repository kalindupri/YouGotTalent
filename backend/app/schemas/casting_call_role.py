import uuid

from pydantic import BaseModel, ConfigDict


class CastingCallRoleCreate(BaseModel):
    title: str
    criteria: str | None = None
    category: str | None = None
    compensation: str | None = None
    guide_track_url: str | None = None


class CastingCallRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    casting_call_id: uuid.UUID
    title: str
    criteria: str | None
    category: str | None
    compensation: str | None
    guide_track_url: str | None

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.casting_call import CastingCallRead


class InvitationCreate(BaseModel):
    talent_id: uuid.UUID
    message: str | None = None


class InvitationStatusUpdate(BaseModel):
    status: str


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    casting_call_id: uuid.UUID
    talent_id: uuid.UUID
    recruiter_id: uuid.UUID
    message: str | None
    status: str
    created_at: datetime
    casting_call: CastingCallRead

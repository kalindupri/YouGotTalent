import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReelCreate(BaseModel):
    url: str
    caption: str | None = None


class ReelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_profile_id: uuid.UUID
    platform: str
    url: str
    caption: str | None
    created_at: datetime

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FollowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_id: uuid.UUID
    recruiter_id: uuid.UUID
    created_at: datetime
    recruiter_company_name: str

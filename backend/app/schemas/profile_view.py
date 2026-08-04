import uuid
from datetime import datetime

from pydantic import BaseModel


class ProfileViewerRead(BaseModel):
    recruiter_id: uuid.UUID
    company_name: str
    viewed_at: datetime


class ProfileViewSummary(BaseModel):
    count: int
    viewers: list[ProfileViewerRead] = []

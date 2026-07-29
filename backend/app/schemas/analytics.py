import uuid

from pydantic import BaseModel

from app.models.casting_call import CastingCallStatus


class CastingCallAnalytics(BaseModel):
    id: uuid.UUID
    title: str
    status: CastingCallStatus
    view_count: int
    application_count: int
    pending_count: int
    shortlisted_count: int
    accepted_count: int
    rejected_count: int


class RecruiterAnalytics(BaseModel):
    total_views: int
    total_applications: int
    response_rate: float
    casting_calls: list[CastingCallAnalytics]

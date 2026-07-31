import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.report import ReportCategory, ReportStatus, ReportTargetType


class ReportCreate(BaseModel):
    category: ReportCategory
    target_type: ReportTargetType | None = None
    target_id: uuid.UUID | None = None
    subject: str
    description: str
    page_url: str | None = None


class ReportStatusUpdate(BaseModel):
    status: ReportStatus
    admin_notes: str | None = None


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter_user_id: uuid.UUID
    category: ReportCategory
    target_type: ReportTargetType | None
    target_id: uuid.UUID | None
    subject: str
    description: str
    page_url: str | None
    status: ReportStatus
    admin_notes: str | None
    created_at: datetime
    updated_at: datetime


class ReportWithReporter(ReportRead):
    reporter_email: str

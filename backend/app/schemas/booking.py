import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class BookingCreate(BaseModel):
    start_at: datetime
    end_at: datetime
    message: str | None = None
    casting_call_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def check_time_order(self) -> "BookingCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class BookingStatusUpdate(BaseModel):
    status: str


class BookingAgreementUpdate(BaseModel):
    agreement_document_url: str | None = None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_id: uuid.UUID
    recruiter_id: uuid.UUID
    casting_call_id: uuid.UUID | None
    start_at: datetime
    end_at: datetime
    message: str | None
    status: str
    agreement_status: str
    agreement_document_url: str | None
    created_at: datetime
    talent_display_name: str
    recruiter_company_name: str
    casting_call_title: str | None

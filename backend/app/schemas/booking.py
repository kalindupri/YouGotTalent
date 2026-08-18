import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class BookingCreate(BaseModel):
    # Required for a standalone booking (application_id is None) — a real calendar slot.
    # Optional for an offer (application_id set) — an offer is a hire/contract agreement,
    # not a proposed time, so no date is collected for it.
    start_at: datetime | None = None
    end_at: datetime | None = None
    message: str | None = None
    casting_call_id: uuid.UUID | None = None
    # Set when this booking IS an offer against a specific job application — see
    # request_booking() in api/routes/bookings.py for the ownership/duplicate-offer validation.
    application_id: uuid.UUID | None = None
    # Branded rich-text (HTML) contract drafted by the recruiter for an offer. Sanitized
    # server-side before storage — see app/core/sanitize.py.
    contract_content: str | None = None

    @model_validator(mode="after")
    def check_dates(self) -> "BookingCreate":
        if self.application_id is None:
            if self.start_at is None or self.end_at is None:
                raise ValueError("start_at and end_at are required for a direct booking request")
        if self.start_at is not None or self.end_at is not None:
            if self.start_at is None or self.end_at is None:
                raise ValueError("start_at and end_at must be provided together")
            if self.end_at <= self.start_at:
                raise ValueError("end_at must be after start_at")
        return self


class BookingStatusUpdate(BaseModel):
    status: str


class BookingAgreementSign(BaseModel):
    signature_name: str
    # Required when the talent is under 18: a minor cannot bind themselves to a contract, so
    # the signature must be the registered guardian's, and they must say so explicitly.
    signed_as_guardian: bool = False


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_id: uuid.UUID
    recruiter_id: uuid.UUID
    casting_call_id: uuid.UUID | None
    application_id: uuid.UUID | None
    start_at: datetime | None
    end_at: datetime | None
    message: str | None
    contract_content: str | None
    status: str
    agreement_status: str
    talent_signature_name: str | None
    talent_signed_at: datetime | None
    recruiter_signature_name: str | None
    recruiter_signed_at: datetime | None
    created_at: datetime
    talent_display_name: str
    recruiter_company_name: str
    casting_call_title: str | None
    application_role_title: str | None = None

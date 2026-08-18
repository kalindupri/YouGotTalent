import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class GuardianConsentDocumentRead(BaseModel):
    """Metadata only. `storage_key` is deliberately absent -- it is never sent to any client,
    including admins; the signed-link endpoint is the only route to the file itself.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doc_type: str
    content_type: str
    size_bytes: int
    original_filename: str | None
    uploaded_at: datetime


class GuardianConsentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    talent_profile_id: uuid.UUID
    guardian_full_name: str
    guardian_relationship: str
    guardian_email: str | None
    guardian_phone: str | None
    minor_full_name: str
    minor_date_of_birth: date
    status: str
    consented_scopes: list[str] | None
    decision_reason: str | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    documents: list[GuardianConsentDocumentRead] = []


class AdminGuardianConsentRead(GuardianConsentRead):
    """Adds the context a reviewer needs to make a decision without opening another page."""

    minor_age: int | None = None
    talent_display_name: str | None = None


class GuardianConsentDecision(BaseModel):
    note: str | None = None


class GuardianConsentRejection(BaseModel):
    # Required, and long enough to be a real explanation: the guardian is told why, and this
    # is the record of the decision. The older verification queue has no reason field at all.
    reason: str = Field(min_length=10)


class GuardianConsentRevocation(BaseModel):
    reason: str | None = None


class DocumentLink(BaseModel):
    url: str
    expires_at: datetime

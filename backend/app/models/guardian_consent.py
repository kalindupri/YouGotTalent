"""Guardian consent for a talent profile belonging to someone under 18.

Under Sri Lanka's Personal Data Protection Act No. 9 of 2022, a child's personal data is a
*special category*, and consent means the consent of the parent or legal guardian. The Act also
names the evidence standard -- a certified copy of the birth certificate, or another document
proving legal guardianship -- which is what guardian_consent_documents holds.

Statuses are String(20) backed by a Python enum, matching TalentProfile.tier and Media.media_type
rather than native Postgres enums, so adding a status later never needs an ALTER TYPE.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import ARRAY, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GuardianConsentStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"  # adult, or the talent has since turned 18
    REQUIRED = "required"  # a minor's profile exists, nothing submitted yet
    SUBMITTED = "submitted"  # awaiting admin review
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"  # guardian withdrew consent
    EXPIRED = "expired"  # annual re-confirmation lapsed


# What the guardian is agreeing to, recorded individually -- the PDPA expects consent to be
# specific rather than one blanket opt-in.
CONSENT_SCOPES = ["profile_public", "media_public", "recruiter_contact", "paid_engagement"]

DOCUMENT_TYPES = ["birth_certificate", "guardian_id", "guardianship_order"]

GUARDIAN_RELATIONSHIPS = ["mother", "father", "legal_guardian"]


class GuardianConsent(Base):
    __tablename__ = "guardian_consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # The account that submitted this. Distinct from the names below: the account holder and
    # the legally responsible guardian should be the same person, but we record what was
    # actually claimed rather than inferring it.
    guardian_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    guardian_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    guardian_relationship: Mapped[str] = mapped_column(String(40), nullable=False)
    guardian_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    guardian_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # The child's legal name. The profile itself carries only a stage name (following how
    # Backstage and Spotlight handle young performers), but the birth certificate being
    # reviewed carries the legal one, so the reviewer needs both to match them up.
    minor_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Snapshot at consent time. If the profile's date of birth is later corrected, an approved
    # consent shouldn't silently start describing a different child.
    minor_date_of_birth: Mapped[Date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=GuardianConsentStatus.REQUIRED.value)
    consented_scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String(40)), nullable=True)

    # Which wording was agreed to, and the exact sentence shown. Costs nothing to store and is
    # the difference between "they consented" and being able to show what they consented to.
    terms_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    privacy_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consent_statement: Mapped[str | None] = mapped_column(Text, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # 45 fits IPv6
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Python-side default, not server_default=func.now(): tests run inside one transaction, and
    # Postgres now() is transaction-scoped, so several rows inserted in one test would share a
    # timestamp and their ordering would be ambiguous.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )

    documents: Mapped[list["GuardianConsentDocument"]] = relationship(
        "GuardianConsentDocument", back_populates="consent", cascade="all, delete-orphan"
    )
    events: Mapped[list["GuardianConsentEvent"]] = relationship(
        "GuardianConsentEvent",
        back_populates="consent",
        cascade="all, delete-orphan",
        order_by="GuardianConsentEvent.created_at.asc()",
    )


class GuardianConsentDocument(Base):
    """Proof of guardianship. Stored in the PRIVATE container -- `storage_key` is an opaque
    key, never a URL, and the only way to read one back is the admin-only signed-link route.
    """

    __tablename__ = "guardian_consent_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guardian_consent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("guardian_consents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Lets a reviewer spot the same document submitted twice, and detects silent substitution.
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )

    consent: Mapped["GuardianConsent"] = relationship("GuardianConsent", back_populates="documents")


class GuardianConsentEvent(Base):
    """Append-only history of every status change.

    The existing talent-verification flow approves and rejects into near-identical state, with
    no reason, no actor and no history -- which is fine for a badge and not fine for a record
    of who allowed a child's data to be processed.
    """

    __tablename__ = "guardian_consent_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guardian_consent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("guardian_consents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    # Null means the system did it (e.g. automatic expiry), not that nobody is accountable.
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )

    consent: Mapped["GuardianConsent"] = relationship("GuardianConsent", back_populates="events")

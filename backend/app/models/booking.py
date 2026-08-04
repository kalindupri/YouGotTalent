import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

BOOKING_STATUSES = ["pending", "accepted", "declined", "cancelled"]
# "not_required" until a booking is accepted, then "pending" until BOTH parties have typed
# their name to sign (talent_signed_at and recruiter_signed_at both set), at which point it
# becomes "signed". This is an in-app typed signature, not a third-party e-signature
# provider (DocuSign or similar) — the "document" is the booking's own terms plus both
# signatures and timestamps.
AGREEMENT_STATUSES = ["not_required", "pending", "signed"]


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)
    casting_call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("casting_calls.id", ondelete="SET NULL"), nullable=True
    )

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    agreement_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_required")

    talent_signature_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    talent_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recruiter_signature_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recruiter_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    talent: Mapped["TalentProfile"] = relationship("TalentProfile")
    recruiter: Mapped["RecruiterProfile"] = relationship("RecruiterProfile")
    casting_call: Mapped["CastingCall | None"] = relationship("CastingCall")

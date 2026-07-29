import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

BOOKING_STATUSES = ["pending", "accepted", "declined", "cancelled"]
# "not_required" until a booking is accepted, then "pending" until either party marks it
# "signed". This is a manual placeholder — no real e-signature provider (DocuSign or
# similar) is wired up yet; agreement_document_url just links to wherever the signed
# document actually lives (uploaded elsewhere).
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
    agreement_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    talent: Mapped["TalentProfile"] = relationship("TalentProfile")
    recruiter: Mapped["RecruiterProfile"] = relationship("RecruiterProfile")
    casting_call: Mapped["CastingCall | None"] = relationship("CastingCall")

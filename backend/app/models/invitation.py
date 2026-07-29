import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

INVITATION_STATUSES = ["pending", "accepted", "declined"]


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (UniqueConstraint("casting_call_id", "talent_id", name="uq_invitation_casting_call_talent"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    casting_call_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("casting_calls.id", ondelete="CASCADE"), nullable=False)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)

    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Plain string, not a native enum, so adding a status later doesn't require an ALTER TYPE migration.
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    casting_call: Mapped["CastingCall"] = relationship("CastingCall")
    talent: Mapped["TalentProfile"] = relationship("TalentProfile")
    recruiter: Mapped["RecruiterProfile"] = relationship("RecruiterProfile")

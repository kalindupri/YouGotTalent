import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("role_id", "talent_id", name="uq_application_role_talent"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    casting_call_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("casting_calls.id", ondelete="CASCADE"), nullable=False)
    # Which specific role/stream within the casting call this application targets — a job post
    # can have several independently-applicable roles (e.g. "Models", "Actors/Performers").
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("casting_call_roles.id", ondelete="CASCADE"), nullable=False)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)

    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Link to the talent's performed take on the audition brief (e.g. a video/audio upload link).
    submission_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus, name="application_status"), default=ApplicationStatus.PENDING, nullable=False)

    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    casting_call: Mapped["CastingCall"] = relationship("CastingCall", back_populates="applications")
    role: Mapped["CastingCallRole"] = relationship("CastingCallRole", back_populates="applications")
    talent: Mapped["TalentProfile"] = relationship("TalentProfile", back_populates="applications")

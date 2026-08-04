import enum
import uuid
from datetime import date, datetime

from sqlalchemy import ARRAY, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.talent_profile import TalentCategory


class CastingCallStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class CastingCall(Base):
    __tablename__ = "casting_calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[TalentCategory] = mapped_column(String(50), nullable=False)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    compensation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    application_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[CastingCallStatus] = mapped_column(Enum(CastingCallStatus, name="casting_call_status"), default=CastingCallStatus.OPEN, nullable=False)

    # What the applicant should actually perform/submit for this audition (e.g. "read this
    # monologue", "cover this song"), plus an optional link to the script/sheet music/reference.
    audition_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    audition_reference_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Short descriptive badges shown on the listing card, e.g. "Product Demo / Explainer Video".
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(60)), nullable=True)
    # Free-form shoot logistics, e.g. "Shoots remotely at home." — distinct from the short
    # `location` tag, which is just a place name used for filtering.
    shoot_details: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Incremented each time the public detail page is loaded — a simple view counter for the
    # recruiter's own analytics, not a unique-visitor count.
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Premium-recruiter-only to set; when true, only premium talent can apply (still visible to
    # everyone in listings — hiding it entirely would waste the upgrade-FOMO effect).
    premium_talent_only: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    recruiter: Mapped["RecruiterProfile"] = relationship("RecruiterProfile", back_populates="casting_calls")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="casting_call", cascade="all, delete-orphan")
    roles: Mapped[list["CastingCallRole"]] = relationship(
        "CastingCallRole", back_populates="casting_call", cascade="all, delete-orphan", order_by="CastingCallRole.created_at"
    )

    @property
    def is_featured(self) -> bool:
        return self.recruiter.tier == "premium"

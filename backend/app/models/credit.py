import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

CREDIT_PROJECT_TYPES = [
    "film",
    "television",
    "commercial",
    "theatre",
    "voice",
    "music",
    "event",
    "online",
    "other",
]


class Credit(Base):
    """A past project on a talent's résumé (StarNow calls this 'Credits & Experience')."""

    __tablename__ = "credits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)

    project_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_or_director: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    talent_profile: Mapped["TalentProfile"] = relationship("TalentProfile", back_populates="credits")

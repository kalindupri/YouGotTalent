import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CastingCallRole(Base):
    __tablename__ = "casting_call_roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    casting_call_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("casting_calls.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Free-form eligibility line shown under the title, e.g. "Content Creators, Female, 18+".
    criteria: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Plain string rather than a TalentCategory FK/enum, since a role's category here is only
    # used for icon/label display and doesn't need to be validated against the fixed list.
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    compensation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Singing-audition guide: guide_track has the recruiter's reference vocal (for the talent to
    # learn from, never mixed into anything); instrumental_track is the music-only backing track
    # a talent's own recorded take gets mixed onto. Both optional -- only set for roles that use
    # the guided-audition flow.
    guide_track_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instrumental_track_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    casting_call: Mapped["CastingCall"] = relationship("CastingCall", back_populates="roles")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="role")

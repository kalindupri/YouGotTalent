import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecruiterProfile(Base):
    __tablename__ = "recruiter_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Holds either a company/agency name or an individual's own name — "company_name" is a
    # historical column name kept for the free-tier/casting-call relationships already built
    # around it; recruiter_type is what actually distinguishes the two.
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recruiter_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="agency")
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verification_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, server_default="free")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="recruiter_profile")
    casting_calls: Mapped[list["CastingCall"]] = relationship("CastingCall", back_populates="recruiter", cascade="all, delete-orphan")
    saved_searches: Mapped[list["SavedSearch"]] = relationship("SavedSearch", back_populates="recruiter", cascade="all, delete-orphan")

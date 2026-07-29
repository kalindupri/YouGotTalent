import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

REVIEWER_ROLES = ["talent", "recruiter"]


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("booking_id", "reviewer_role", name="uq_review_booking_reviewer_role"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)

    # Who wrote this review: "talent" (rating the recruiter) or "recruiter" (rating the talent).
    reviewer_role: Mapped[str] = mapped_column(String(20), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking: Mapped["Booking"] = relationship("Booking")
    talent: Mapped["TalentProfile"] = relationship("TalentProfile")
    recruiter: Mapped["RecruiterProfile"] = relationship("RecruiterProfile")

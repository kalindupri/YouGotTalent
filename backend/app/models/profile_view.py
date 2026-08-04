import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProfileView(Base):
    """One row per profile visit by a logged-in recruiter — an activity log, not a bookmark
    (unlike SavedTalent), so there's deliberately no unique constraint here.
    """

    __tablename__ = "profile_views"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)

    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    recruiter: Mapped["RecruiterProfile"] = relationship("RecruiterProfile")

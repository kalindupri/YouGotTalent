import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.content_visibility import ContentVisibility

REEL_PLATFORMS = ["tiktok", "instagram", "facebook"]


class Reel(Base):
    """A Premium talent's showcased TikTok / Instagram Reels / Facebook Reels link."""

    __tablename__ = "reels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)

    # Derived server-side from the URL's hostname at creation time — never trust a
    # client-supplied platform label.
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    visibility: Mapped[ContentVisibility] = mapped_column(String(20), nullable=False, server_default="public")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    talent_profile: Mapped["TalentProfile"] = relationship("TalentProfile", back_populates="reels")

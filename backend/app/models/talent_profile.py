import enum
import uuid
from datetime import date, datetime

from sqlalchemy import ARRAY, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TalentCategory(str, enum.Enum):
    ACTING = "acting"
    SINGING = "singing"
    DANCING = "dancing"
    PAINTING = "painting"
    SCRIPT_WRITING = "script_writing"
    PHOTOGRAPHY = "photography"
    MUSIC = "music"
    CHOREOGRAPHY = "choreography"
    COMEDY = "comedy"
    VOICE_OVER = "voice_over"
    DIRECTION = "direction"
    MODELING = "modeling"
    DESIGN = "design"
    OTHER = "other"


class TalentProfile(Base):
    __tablename__ = "talent_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Stored as plain text (not a Postgres native enum) so new skill categories can be
    # added in TalentCategory without an ALTER TYPE migration.
    category: Mapped[TalentCategory] = mapped_column(String(50), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skills: Mapped[list[str] | None] = mapped_column(ARRAY(String(60)), nullable=True)

    # Plain string, not a native enum, for the same reason as `category`: adding a tier
    # later (e.g. "pro") shouldn't require an ALTER TYPE migration.
    tier: Mapped[str] = mapped_column(String(20), nullable=False, server_default="free")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    verification_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Whether this talent wants "a new job matching your category was just posted" emails.
    job_alert_emails: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tiktok_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # A single featured intro/pitch video shown at the top of the profile — distinct from
    # the general portfolio media list, which can hold many auditions of any type.
    intro_video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Free-form key/value store for category-specific detail (height/build/eye color for
    # acting, vocal range for singing, camera gear for photography, etc). Which keys are
    # asked for and shown is driven entirely by frontend config per TalentCategory, so new
    # attributes for a category never require a migration.
    attributes: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="talent_profile")
    media: Mapped[list["Media"]] = relationship("Media", back_populates="talent_profile", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="talent", cascade="all, delete-orphan")
    credits: Mapped[list["Credit"]] = relationship(
        "Credit", back_populates="talent_profile", cascade="all, delete-orphan", order_by="Credit.created_at.desc()"
    )

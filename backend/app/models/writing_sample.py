import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.content_visibility import ContentVisibility

WRITING_TYPES = ["novel", "script", "song", "poem", "other"]
WRITING_LANGUAGES = ["sinhala", "tamil", "english", "other"]

DEFAULT_VISIBLE_LINES = 8


class WritingSample(Base):
    """A writer's piece (novel excerpt, screenplay, song lyrics, poem, ...). Kept as a draft
    (never returned to non-owner viewers) until the talent explicitly publishes it. Once
    published, only the first `visible_lines` lines of `body` are ever sent to a non-owner
    viewer -- the writer controls how much of their own work is given away for free, same
    motivation as a recruiter only getting a script's first page rather than the whole thing.
    """

    __tablename__ = "writing_samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Plain strings, not native enums -- same reasoning as `category`/`tier` elsewhere: adding
    # a new writing type or language later shouldn't require an ALTER TYPE migration.
    writing_type: Mapped[str] = mapped_column(String(20), nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # How many lines of `body` a non-owner viewer is shown. Enforced server-side when
    # serializing for anyone other than the owner -- see crud/writing_sample.py:to_read_schema.
    visible_lines: Mapped[int] = mapped_column(Integer, nullable=False, server_default=str(DEFAULT_VISIBLE_LINES))

    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    visibility: Mapped[ContentVisibility] = mapped_column(String(20), nullable=False, server_default="public")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    talent_profile: Mapped["TalentProfile"] = relationship("TalentProfile", back_populates="writing_samples")


# Writing samples are for people who write: scriptwriters, and songwriters/lyricists (who sit
# under `music` in TalentCategory -- there is no separate songwriting category). A talent with
# any of these among their categories can add samples.
WRITING_SAMPLE_CATEGORIES = ["script_writing", "music"]


def can_add_writing_samples(profile) -> bool:
    categories = set(profile.categories or [profile.category])
    return bool(categories.intersection(WRITING_SAMPLE_CATEGORIES))

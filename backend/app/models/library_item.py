import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LibraryItem(Base):
    """A persistent, publicly-browsable body-of-work entry — distinct from the audition
    reel (`Media`), which is oriented around a handful of showcase pieces for recruiters.
    Premium-only: the point is a standing catalog talent can keep building over time
    (a "track library" for singers, a portfolio gallery for photographers, etc.)."""

    __tablename__ = "library_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Reuses the same photo/video/audio/document vocabulary as Media (app.models.media.MediaType)
    # rather than importing that enum directly, since a library item isn't a Media row and
    # shouldn't be coupled to that table's lifecycle.
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)

    # Python-side default (not server_default=func.now()) since Postgres's now() is frozen for
    # the whole transaction — under the test harness's SAVEPOINT-per-commit isolation, multiple
    # items created in one test would otherwise get identical timestamps and sort ambiguously.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    talent: Mapped["TalentProfile"] = relationship("TalentProfile")

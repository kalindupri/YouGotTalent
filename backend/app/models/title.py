import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkType(str, enum.Enum):
    FILM = "film"
    TV_SERIES = "tv_series"
    SONG = "song"


class Title(Base):
    """A film, TV series, or song that users can rate and critique — the catalog entry
    Sri Lanka's marketplace doesn't have a good equivalent of yet.
    """

    __tablename__ = "titles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    work_type: Mapped[WorkType] = mapped_column(Enum(WorkType, name="work_type"), nullable=False)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    genre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    added_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    added_by: Mapped["User"] = relationship("User")
    reviews: Mapped[list["TitleReview"]] = relationship("TitleReview", back_populates="title", cascade="all, delete-orphan")


class TitleReview(Base):
    """A user's rating (required) and optional written critique for a Title — one per
    user per title, upserted on repeat submission (like editing your own review).
    """

    __tablename__ = "title_reviews"
    __table_args__ = (UniqueConstraint("title_id", "user_id", name="uq_title_review_title_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("titles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    title: Mapped["Title"] = relationship("Title", back_populates="reviews")
    user: Mapped["User"] = relationship("User")

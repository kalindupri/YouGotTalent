import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DiscussionCategory(str, enum.Enum):
    FILMS = "films"
    TV_SERIES = "tv_series"
    MUSIC = "music"
    INDUSTRY_NEWS = "industry_news"
    GENERAL = "general"


class DiscussionThread(Base):
    __tablename__ = "discussion_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[DiscussionCategory] = mapped_column(Enum(DiscussionCategory, name="discussion_category"), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Optionally ties a thread to a specific film/TV series/song, e.g. "Let's discuss the ending
    # of X" — nullable since most industry-news/general threads aren't about one title.
    title_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("titles.id", ondelete="SET NULL"), nullable=True)

    author_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped["User"] = relationship("User")
    title: Mapped["Title"] = relationship("Title")
    replies: Mapped[list["DiscussionReply"]] = relationship(
        "DiscussionReply", back_populates="thread", cascade="all, delete-orphan", order_by="DiscussionReply.created_at.asc()"
    )


class DiscussionReply(Base):
    __tablename__ = "discussion_replies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("discussion_threads.id", ondelete="CASCADE"), nullable=False)
    author_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    author: Mapped["User"] = relationship("User")
    thread: Mapped["DiscussionThread"] = relationship("DiscussionThread", back_populates="replies")

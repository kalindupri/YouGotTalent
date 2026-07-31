import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ReportCategory(str, enum.Enum):
    BUG = "bug"
    SPAM = "spam"
    HARASSMENT = "harassment"
    FAKE_PROFILE = "fake_profile"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    OTHER = "other"


class ReportTargetType(str, enum.Enum):
    TALENT_PROFILE = "talent_profile"
    RECRUITER_PROFILE = "recruiter_profile"
    CASTING_CALL = "casting_call"
    MESSAGE = "message"
    TITLE = "title"
    TITLE_REVIEW = "title_review"
    DISCUSSION_THREAD = "discussion_thread"
    DISCUSSION_REPLY = "discussion_reply"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    category: Mapped[ReportCategory] = mapped_column(Enum(ReportCategory, name="report_category"), nullable=False)
    # Null target_type/target_id means a general site issue (e.g. a bug report) with no reported entity.
    target_type: Mapped[ReportTargetType | None] = mapped_column(Enum(ReportTargetType, name="report_target_type"), nullable=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Where the reporter was in the app when they filed a bug report — not meaningful for profile/content reports.
    page_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus, name="report_status"), nullable=False, default=ReportStatus.OPEN)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    reporter: Mapped["User"] = relationship("User")

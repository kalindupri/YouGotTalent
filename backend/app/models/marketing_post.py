import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketingPostStatus(str, enum.Enum):
    AWAITING_TOPIC = "awaiting_topic"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    POSTED = "posted"
    FAILED = "failed"
    EXPIRED = "expired"


class MarketingPost(Base):
    __tablename__ = "marketing_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Null while status=AWAITING_TOPIC — the human hasn't replied with a topic in Discord yet.
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[MarketingPostStatus] = mapped_column(
        Enum(MarketingPostStatus, name="marketing_post_status"), nullable=False, default=MarketingPostStatus.PENDING_APPROVAL
    )

    discord_channel_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    discord_message_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    facebook_post_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

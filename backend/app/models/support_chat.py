import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SupportConversationStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class SupportMessageSender(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"


class SupportConversation(Base):
    """A live-chat handoff from the FAQ bot, relayed through a Discord thread. The thread is the
    real-time transport (the human agent replies from Discord); this table + SupportMessage are
    the app's own durable copy of the transcript.
    """

    __tablename__ = "support_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    guest_label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    discord_thread_id: Mapped[str] = mapped_column(String(32), nullable=False)
    # Snowflake id of the last Discord message we've already synced into SupportMessage, so
    # polling only fetches what's new instead of re-scanning the whole thread every time.
    last_seen_discord_message_id: Mapped[str | None] = mapped_column(String(32), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default=SupportConversationStatus.OPEN.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    messages: Mapped[list["SupportMessage"]] = relationship(
        "SupportMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="SupportMessage.created_at"
    )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("support_conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    conversation: Mapped["SupportConversation"] = relationship("SupportConversation", back_populates="messages")

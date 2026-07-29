import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class Media(Base):
    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)

    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    media_type: Mapped[MediaType] = mapped_column(String(20), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_cover: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    talent_profile: Mapped["TalentProfile"] = relationship("TalentProfile", back_populates="media")

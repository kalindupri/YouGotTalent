import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SavedTalent(Base):
    __tablename__ = "saved_talents"
    __table_args__ = (UniqueConstraint("recruiter_id", "talent_id", name="uq_saved_talent_recruiter_talent"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    talent: Mapped["TalentProfile"] = relationship("TalentProfile")

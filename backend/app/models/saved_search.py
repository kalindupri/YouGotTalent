import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    q: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verified_only: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    recruiter: Mapped["RecruiterProfile"] = relationship("RecruiterProfile", back_populates="saved_searches")

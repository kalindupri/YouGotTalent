import uuid
from datetime import datetime, time

from sqlalchemy import DateTime, ForeignKey, Integer, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AvailabilityWindow(Base):
    __tablename__ = "availability_windows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)

    # 0=Monday .. 6=Sunday (Python's date.weekday() convention), so a window recurs weekly.
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    talent: Mapped["TalentProfile"] = relationship("TalentProfile")

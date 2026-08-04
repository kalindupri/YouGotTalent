import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TalentList(Base):
    """A recruiter-owned named list (e.g. "Monsoon Diaries - Lead") for organizing candidates
    into per-project pipelines — an additional layer on top of the simple SavedTalent bookmark,
    not a replacement for it.
    """

    __tablename__ = "talent_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    members: Mapped[list["TalentListMember"]] = relationship(
        "TalentListMember", back_populates="list", cascade="all, delete-orphan", order_by="TalentListMember.created_at"
    )


class TalentListMember(Base):
    __tablename__ = "talent_list_members"
    __table_args__ = (UniqueConstraint("list_id", "talent_id", name="uq_talent_list_member_list_talent"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_lists.id", ondelete="CASCADE"), nullable=False)
    talent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    list: Mapped["TalentList"] = relationship("TalentList", back_populates="members")
    talent: Mapped["TalentProfile"] = relationship("TalentProfile")

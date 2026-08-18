import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    TALENT = "talent"
    RECRUITER = "recruiter"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    consent_given_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # New registrations start unverified and must confirm via the emailed code before they can
    # log in; existing accounts are backfilled to verified via the migration's server_default.
    email_verified: Mapped[bool] = mapped_column(default=True, server_default="true", nullable=False)
    verification_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    verification_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Separate from verification_code above so a password-reset request can't clobber a pending
    # email-verification code (and vice versa) if a user triggers both around the same time.
    password_reset_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    password_reset_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # A list, not a single profile: a parent/legal guardian holds one account and may manage a
    # profile per child. Ordinary adult talent have exactly one. Use get_current_talent_profile
    # to resolve "which profile is this request acting as".
    talent_profiles: Mapped[list["TalentProfile"]] = relationship(
        "TalentProfile", back_populates="user", cascade="all, delete-orphan"
    )
    recruiter_profile: Mapped["RecruiterProfile | None"] = relationship("RecruiterProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

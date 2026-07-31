import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.subscription import SubscriptionPlan


class PricingVersion(Base):
    """One row per price change — the current price for a plan is simply its most recent row.
    Existing Subscription rows are never touched by a new version; they keep the price_lkr they
    were charged at, so this table only ever affects what NEW checkouts get quoted.
    """

    __tablename__ = "pricing_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan, name="subscription_plan"), nullable=False)
    monthly_price_lkr: Mapped[int] = mapped_column(Integer, nullable=False)
    # Client-side default rather than server_default=func.now() — Postgres's now() is
    # transaction-scoped, so two versions inserted in the same transaction (e.g. two admin price
    # changes back to back in a test) would otherwise get an identical created_at and make
    # "most recent version" ordering ambiguous.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    created_by: Mapped["User"] = relationship("User")

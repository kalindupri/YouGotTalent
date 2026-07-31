import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SubscriptionPlan(str, enum.Enum):
    TALENT_PREMIUM = "talent_premium"
    RECRUITER_PREMIUM = "recruiter_premium"


class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class SubscriptionStatus(str, enum.Enum):
    TRIALING = "trialing"
    # Checkout has started at the gateway but the webhook confirming payment hasn't arrived yet.
    PENDING = "pending"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"


class PaymentGatewayName(str, enum.Enum):
    MOCK = "mock"
    PAYHERE = "payhere"
    STRIPE = "stripe"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Exactly one of these is set — mirrors the loose per-side FK pattern used elsewhere in this
    # codebase (e.g. Report.target_type/target_id) rather than a single polymorphic column.
    talent_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("talent_profiles.id", ondelete="CASCADE"), nullable=True
    )
    recruiter_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recruiter_profiles.id", ondelete="CASCADE"), nullable=True
    )

    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan, name="subscription_plan"), nullable=False)
    billing_cycle: Mapped[BillingCycle] = mapped_column(Enum(BillingCycle, name="billing_cycle"), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus, name="subscription_status"), nullable=False)
    gateway: Mapped[PaymentGatewayName] = mapped_column(Enum(PaymentGatewayName, name="payment_gateway_name"), nullable=False)

    gateway_subscription_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gateway_customer_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Snapshot of what this subscriber actually pays — set once at signup and never overwritten
    # by later price changes, so a founding-member rate sticks for the life of the subscription.
    price_lkr: Mapped[int] = mapped_column(Integer, nullable=False)

    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    talent_profile: Mapped["TalentProfile"] = relationship("TalentProfile")
    recruiter_profile: Mapped["RecruiterProfile"] = relationship("RecruiterProfile")

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
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


class CancellationReason(str, enum.Enum):
    TOO_EXPENSIVE = "too_expensive"
    NOT_USING_ENOUGH = "not_using_enough"
    MISSING_FEATURES = "missing_features"
    SWITCHING_PLATFORM = "switching_platform"
    TEMPORARY_PAUSE = "temporary_pause"
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


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

    @property
    def effective_price_lkr(self) -> int:
        """price_lkr discounted if a retention offer is still within its window."""
        if self.discount_percent and self.discount_expires_at:
            expires = self.discount_expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < expires:
                return round(self.price_lkr * (1 - self.discount_percent / 100))
        return self.price_lkr

    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # The subscriber keeps premium access through current_period_end even after requesting
    # cancellation — only sync_if_expired/run_dunning_sweep flips status to CANCELED once that
    # date actually passes, per "subscription should remain until the paid period".
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    canceled_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason_category: Mapped[CancellationReason | None] = mapped_column(
        Enum(CancellationReason, name="cancellation_reason"), nullable=True
    )
    cancellation_reason_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Retention discount — a one-time offer shown when a subscriber tries to cancel.
    retention_offer_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    discount_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Dunning: when a renewal payment first fails, the subscriber keeps access (see
    # _PREMIUM_STATUSES) for a grace period, with a reminder partway through — see
    # settings.PAST_DUE_GRACE_DAYS and crud/subscription.py's run_dunning_sweep.
    past_due_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    past_due_reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    talent_profile: Mapped["TalentProfile"] = relationship("TalentProfile")
    recruiter_profile: Mapped["RecruiterProfile"] = relationship("RecruiterProfile")
    payments: Mapped[list["SubscriptionPayment"]] = relationship(
        "SubscriptionPayment", back_populates="subscription", cascade="all, delete-orphan", order_by="SubscriptionPayment.created_at.desc()"
    )


class SubscriptionPayment(Base):
    """One row per payment attempt (success or failure) — the ledger admins use to see what a
    subscriber has actually been charged, distinct from the current live state on Subscription.
    """

    __tablename__ = "subscription_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)

    amount_lkr: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), nullable=False)
    gateway: Mapped[PaymentGatewayName] = mapped_column(Enum(PaymentGatewayName, name="payment_gateway_name"), nullable=False)
    gateway_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)

    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="payments")

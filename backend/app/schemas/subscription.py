import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.subscription import (
    BillingCycle,
    CancellationReason,
    PaymentGatewayName,
    PaymentStatus,
    SubscriptionPlan,
    SubscriptionStatus,
)


class CheckoutRequest(BaseModel):
    billing_cycle: BillingCycle = BillingCycle.MONTHLY


class CheckoutResponse(BaseModel):
    redirect_url: str
    method: str
    fields: dict[str, str] = {}


class CancelRequest(BaseModel):
    reason_category: CancellationReason
    reason_detail: str | None = None


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan: SubscriptionPlan
    billing_cycle: BillingCycle
    status: SubscriptionStatus
    gateway: PaymentGatewayName
    price_lkr: int
    effective_price_lkr: int
    trial_end: datetime | None
    current_period_end: datetime | None
    canceled_at: datetime | None
    cancel_at_period_end: bool
    canceled_requested_at: datetime | None
    cancellation_reason_category: CancellationReason | None
    cancellation_reason_detail: str | None
    retention_offer_used: bool
    discount_percent: int | None
    discount_expires_at: datetime | None
    past_due_since: datetime | None


class RetentionOfferRead(BaseModel):
    available: bool
    discount_percent: int
    discount_months: int


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount_lkr: int
    status: PaymentStatus
    gateway: PaymentGatewayName
    gateway_reference: str | None
    period_start: datetime | None
    period_end: datetime | None
    failure_reason: str | None
    created_at: datetime

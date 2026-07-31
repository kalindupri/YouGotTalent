import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.subscription import BillingCycle, PaymentGatewayName, SubscriptionPlan, SubscriptionStatus


class CheckoutRequest(BaseModel):
    billing_cycle: BillingCycle = BillingCycle.MONTHLY


class CheckoutResponse(BaseModel):
    redirect_url: str
    method: str
    fields: dict[str, str] = {}


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan: SubscriptionPlan
    billing_cycle: BillingCycle
    status: SubscriptionStatus
    gateway: PaymentGatewayName
    price_lkr: int
    trial_end: datetime | None
    current_period_end: datetime | None
    canceled_at: datetime | None

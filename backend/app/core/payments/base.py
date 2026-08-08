from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.models.subscription import PaymentGatewayName, Subscription


@dataclass
class CheckoutSession:
    """Where to send the subscriber to pay, and how to get them there.

    method is "get" for a plain redirect link (Stripe Checkout, the mock gateway), or "post" for
    a gateway that expects an auto-submitting HTML form of hidden fields (PayHere's checkout).
    """

    redirect_url: str
    method: str
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class WebhookEvent:
    """Normalized result of a verified gateway webhook call.

    our_subscription_id identifies the row directly when the gateway can echo back an
    identifier we chose (PayHere's order_id, Stripe's client_reference_id) — this is how the
    very first "checkout completed" event gets matched. Later lifecycle events (renewal,
    cancellation) usually only carry the gateway's own subscription id, so callers fall back to
    matching on gateway_subscription_id once it's been recorded on the row.
    """

    status: str  # matches a SubscriptionStatus value
    our_subscription_id: str | None = None
    gateway_subscription_id: str | None = None
    current_period_end: datetime | None = None


class PaymentGateway(ABC):
    name: PaymentGatewayName

    # True for gateways with no real external step (the mock gateway) — the caller activates
    # the subscription immediately instead of waiting for a webhook.
    activates_immediately: bool = False

    @abstractmethod
    def start_checkout(self, subscription: Subscription, return_url: str, trial_days: int = 0) -> CheckoutSession: ...

    @abstractmethod
    def verify_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent | None: ...

    @abstractmethod
    def cancel(self, subscription: Subscription) -> None: ...

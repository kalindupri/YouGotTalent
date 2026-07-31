from app.core.payments.base import CheckoutSession, PaymentGateway, WebhookEvent
from app.models.subscription import PaymentGatewayName, Subscription


class MockGateway(PaymentGateway):
    """Activates a subscription instantly with no external call or real charge.

    This is the default gateway (settings.PAYMENT_GATEWAY = "mock") so every environment —
    local dev, CI, a fresh clone — works out of the box with zero payment-provider setup.
    Switch to "payhere" or "stripe" once real merchant credentials exist.
    """

    name = PaymentGatewayName.MOCK
    activates_immediately = True

    def start_checkout(self, subscription: Subscription, return_url: str) -> CheckoutSession:
        return CheckoutSession(redirect_url=f"{return_url}?mock=1", method="get")

    def verify_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent | None:
        # Nothing ever posts a webhook to the mock gateway — activates_immediately handles it.
        return None

    def cancel(self, subscription: Subscription) -> None:
        pass

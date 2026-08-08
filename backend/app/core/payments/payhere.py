import hashlib

from app.core.config import settings
from app.core.payments.base import CheckoutSession, PaymentGateway, WebhookEvent
from app.models.subscription import BillingCycle, PaymentGatewayName, Subscription

# PayHere status_code values from their notify_url payload.
_STATUS_MAP = {
    "2": "active",  # success
    "0": "pending",
    "-1": "canceled",
    "-2": "past_due",  # failed — treated as a missed payment, not an immediate cancellation
    "-3": "past_due",  # chargedback
}


def _hash(*parts: str) -> str:
    return hashlib.md5("".join(parts).encode()).hexdigest().upper()


class PayHereGateway(PaymentGateway):
    """Sri Lanka's standard LKR payment gateway (Stripe isn't available to LK merchants
    directly). Implements PayHere's documented Checkout + recurring-billing protocol:
    https://support.payhere.lk/api-&-mobile-sdk/payhere-checkout

    Requires PAYHERE_MERCHANT_ID and PAYHERE_MERCHANT_SECRET from a real PayHere merchant
    account — until those are set, app/core/payments/factory.py won't select this gateway.
    """

    name = PaymentGatewayName.PAYHERE

    def start_checkout(self, subscription: Subscription, return_url: str, trial_days: int = 0) -> CheckoutSession:
        # trial_days isn't wired up here yet — PayHere's recurring-billing fields (recurrence/
        # duration) don't have a documented free-trial equivalent to the ones used below. Not
        # urgent since no live PayHere merchant account is configured yet.
        order_id = str(subscription.id)
        amount = f"{subscription.price_lkr:.2f}"
        merchant_secret_hash = _hash(settings.PAYHERE_MERCHANT_SECRET or "")
        signature = _hash(settings.PAYHERE_MERCHANT_ID or "", order_id, amount, "LKR", merchant_secret_hash)

        item_name = subscription.plan.value.replace("_", " ").title()
        recurrence = "1 Year" if subscription.billing_cycle == BillingCycle.ANNUAL else "1 Month"

        fields = {
            "merchant_id": settings.PAYHERE_MERCHANT_ID or "",
            "return_url": return_url,
            "cancel_url": return_url,
            "notify_url": f"{settings.BACKEND_PUBLIC_URL}/api/v1/billing/webhook/payhere",
            "order_id": order_id,
            "items": item_name,
            "currency": "LKR",
            "amount": amount,
            "recurrence": recurrence,
            "duration": "Forever",
            "hash": signature,
        }
        base_url = "https://sandbox.payhere.lk/pay/checkout" if settings.PAYHERE_SANDBOX else "https://www.payhere.lk/pay/checkout"
        return CheckoutSession(redirect_url=base_url, method="post", fields=fields)

    def verify_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent | None:
        from urllib.parse import parse_qsl

        form = dict(parse_qsl(payload.decode()))
        merchant_id = form.get("merchant_id", "")
        order_id = form.get("order_id", "")
        amount = form.get("payhere_amount", "")
        currency = form.get("payhere_currency", "")
        status_code = form.get("status_code", "")
        received_sig = form.get("md5sig", "")

        merchant_secret_hash = _hash(settings.PAYHERE_MERCHANT_SECRET or "")
        expected_sig = _hash(merchant_id, order_id, amount, currency, status_code, merchant_secret_hash)
        if not received_sig or received_sig != expected_sig:
            return None

        status = _STATUS_MAP.get(status_code)
        if status is None:
            return None
        return WebhookEvent(
            status=status,
            our_subscription_id=order_id,
            gateway_subscription_id=form.get("subscription_id") or None,
        )

    def cancel(self, subscription: Subscription) -> None:
        # PayHere recurring subscriptions are canceled through their separate Subscription
        # Management API (a distinct OAuth app_id/app_secret from the checkout merchant
        # credentials above). Wire that call up once a real merchant account exists — for now
        # this only stops our own renewal tracking; the actual PayHere-side recurring charge
        # must be canceled from the PayHere merchant dashboard until that API call is added.
        pass

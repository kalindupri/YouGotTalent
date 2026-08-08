import stripe

from app.core.config import settings
from app.core.payments.base import CheckoutSession, PaymentGateway, WebhookEvent
from app.models.subscription import BillingCycle, PaymentGatewayName, Subscription, SubscriptionPlan


class StripeGateway(PaymentGateway):
    """International path — for expanding beyond Sri Lanka once Stripe support is worth adding.
    Stripe doesn't settle in LKR, so this path charges STRIPE_CURRENCY/STRIPE_*_PRICE instead of
    the LKR prices used by PayHere; those are configured separately in app/core/config.py.

    Requires STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET from a real Stripe account — until
    those are set, app/core/payments/factory.py won't select this gateway.
    """

    name = PaymentGatewayName.STRIPE

    def start_checkout(self, subscription: Subscription, return_url: str) -> CheckoutSession:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        is_talent = subscription.plan == SubscriptionPlan.TALENT_PREMIUM
        price_id = settings.STRIPE_TALENT_PRICE_ID if is_talent else settings.STRIPE_RECRUITER_PRICE_ID

        # Prefer a pre-created Price object from the Stripe dashboard (monthly only, for now —
        # there's no separate annual Price ID configured yet). Falls back to building price_data
        # inline, which is the only option for the annual cycle.
        if price_id and subscription.billing_cycle == BillingCycle.MONTHLY:
            line_item = {"price": price_id, "quantity": 1}
        else:
            unit_amount = settings.STRIPE_TALENT_PRICE if is_talent else settings.STRIPE_RECRUITER_PRICE
            if subscription.billing_cycle == BillingCycle.ANNUAL:
                unit_amount *= settings.ANNUAL_BILLING_MONTHS_CHARGED
            interval = "year" if subscription.billing_cycle == BillingCycle.ANNUAL else "month"
            product_name = subscription.plan.value.replace("_", " ").title()
            line_item = {
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": {"name": product_name},
                    "unit_amount": unit_amount,
                    "recurring": {"interval": interval},
                },
                "quantity": 1,
            }

        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[line_item],
            success_url=f"{return_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=return_url,
            client_reference_id=str(subscription.id),
        )
        return CheckoutSession(redirect_url=session.url, method="get")

    def verify_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent | None:
        try:
            event = stripe.Webhook.construct_event(payload, headers.get("stripe-signature", ""), settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.SignatureVerificationError):
            return None

        obj = event["data"]["object"]

        def field(key: str) -> str | None:
            try:
                return obj[key]
            except (KeyError, AttributeError):
                return None

        if event["type"] == "checkout.session.completed":
            return WebhookEvent(status="active", our_subscription_id=field("client_reference_id"), gateway_subscription_id=field("subscription"))
        if event["type"] == "invoice.payment_failed":
            return WebhookEvent(status="past_due", gateway_subscription_id=field("subscription"))
        if event["type"] == "invoice.paid":
            return WebhookEvent(status="active", gateway_subscription_id=field("subscription"))
        if event["type"] == "customer.subscription.deleted":
            return WebhookEvent(status="canceled", gateway_subscription_id=field("id"))
        return None

    def cancel(self, subscription: Subscription) -> None:
        if not subscription.gateway_subscription_id:
            return
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Subscription.delete(subscription.gateway_subscription_id)

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.payments.base import CheckoutSession, PaymentGateway, WebhookEvent
from app.core.payments.factory import get_gateway
from app.core.payments.payhere import PayHereGateway
from app.core.payments.stripe_gateway import StripeGateway
from app.crud import subscription as subscription_crud
from app.main import app
from app.models.subscription import PaymentGatewayName, Subscription, SubscriptionStatus


def test_upgrade_starts_a_trial(client, talent_headers, talent_profile):
    resp = client.post("/api/v1/talents/me/upgrade", headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["tier"] == "premium"

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "trialing"
    assert body["plan"] == "talent_premium"
    assert body["price_lkr"] == settings.PREMIUM_TALENT_PRICE_LKR
    assert body["trial_end"] is not None


def test_recruiter_upgrade_starts_a_trial(client, recruiter_headers, recruiter_profile):
    resp = client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json()["tier"] == "premium"

    resp = client.get("/api/v1/billing/me", headers=recruiter_headers)
    body = resp.json()
    assert body["status"] == "trialing"
    assert body["plan"] == "recruiter_premium"
    assert body["price_lkr"] == settings.PREMIUM_RECRUITER_PRICE_LKR


def test_no_subscription_before_upgrading(client, talent_headers, talent_profile):
    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json() is None


def test_mock_checkout_activates_immediately(client, talent_headers, talent_profile):
    resp = client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["method"] == "get"
    assert "mock=1" in resp.json()["redirect_url"]

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    body = resp.json()
    assert body["status"] == "active"
    assert body["current_period_end"] is not None

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "premium"


def test_annual_checkout_prices_at_ten_months(client, recruiter_headers, recruiter_profile):
    resp = client.post("/api/v1/billing/checkout", json={"billing_cycle": "annual"}, headers=recruiter_headers)
    assert resp.status_code == 201, resp.text

    resp = client.get("/api/v1/billing/me", headers=recruiter_headers)
    body = resp.json()
    assert body["billing_cycle"] == "annual"
    assert body["price_lkr"] == settings.PREMIUM_RECRUITER_PRICE_LKR * settings.ANNUAL_BILLING_MONTHS_CHARGED


def test_cancel_stays_premium_until_period_end(client, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    resp = client.post(
        "/api/v1/billing/cancel",
        json={"reason_category": "too_expensive", "reason_detail": "just testing"},
        headers=talent_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "active"  # still active — cancellation is scheduled, not immediate
    assert body["cancel_at_period_end"] is True
    assert body["cancellation_reason_category"] == "too_expensive"

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "premium"


def test_cancel_without_a_subscription_404s(client, talent_headers, talent_profile):
    resp = client.post(
        "/api/v1/billing/cancel", json={"reason_category": "other"}, headers=talent_headers
    )
    assert resp.status_code == 404


def test_expired_trial_reverts_tier_lazily(client, talent_headers, talent_profile, db_session):
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)

    sub = db_session.query(Subscription).filter(Subscription.talent_profile_id == talent_profile["id"]).first()
    sub.trial_end = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    # Tier only gets reconciled lazily, on the next request that loads the talent profile.
    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "free"

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    assert resp.json()["status"] == "expired"


def test_admin_financial_overview_reflects_real_revenue(client, admin_headers, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)  # trial only, no revenue
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=recruiter_headers)  # paying

    resp = client.get("/api/v1/admin/financial-overview", headers=admin_headers)
    body = resp.json()
    assert body["trialing_subscriptions"] == 1
    assert body["paying_subscriptions"] == 1
    assert body["real_monthly_revenue_lkr"] == settings.PREMIUM_RECRUITER_PRICE_LKR


def test_payhere_webhook_rejects_bad_signature(client):
    resp = client.post(
        "/api/v1/billing/webhook/payhere",
        content="merchant_id=x&order_id=y&payhere_amount=490.00&payhere_currency=LKR&status_code=2&md5sig=bogus",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200  # webhooks always 200 so the gateway doesn't retry forever
    assert resp.json() == {"status": "ok"}


def test_payhere_gateway_verifies_correct_signature(monkeypatch):
    monkeypatch.setattr(settings, "PAYHERE_MERCHANT_ID", "test-merchant")
    monkeypatch.setattr(settings, "PAYHERE_MERCHANT_SECRET", "test-secret")

    order_id = "abc-123"
    amount = "490.00"
    currency = "LKR"
    status_code = "2"
    secret_hash = hashlib.md5(("test-secret").encode()).hexdigest().upper()
    sig = hashlib.md5(("test-merchant" + order_id + amount + currency + status_code + secret_hash).encode()).hexdigest().upper()

    payload = f"merchant_id=test-merchant&order_id={order_id}&payhere_amount={amount}&payhere_currency={currency}&status_code={status_code}&md5sig={sig}"
    event = PayHereGateway().verify_webhook(payload.encode(), {})
    assert event is not None
    assert event.status == "active"
    assert event.our_subscription_id == order_id


def test_payhere_gateway_rejects_tampered_signature(monkeypatch):
    monkeypatch.setattr(settings, "PAYHERE_MERCHANT_ID", "test-merchant")
    monkeypatch.setattr(settings, "PAYHERE_MERCHANT_SECRET", "test-secret")

    payload = "merchant_id=test-merchant&order_id=abc-123&payhere_amount=490.00&payhere_currency=LKR&status_code=2&md5sig=wrong"
    event = PayHereGateway().verify_webhook(payload.encode(), {})
    assert event is None


def _sign_stripe_payload(payload: bytes, secret: str) -> str:
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload.decode()}"
    signature = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def test_stripe_gateway_verifies_correct_signature(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    payload = json.dumps(
        {
            "id": "evt_1",
            "object": "event",
            "type": "checkout.session.completed",
            "data": {"object": {"client_reference_id": "sub-123", "subscription": "sub_stripe_1"}},
        }
    ).encode()
    headers = {"stripe-signature": _sign_stripe_payload(payload, "whsec_test")}

    event = StripeGateway().verify_webhook(payload, headers)
    assert event is not None
    assert event.status == "active"
    assert event.our_subscription_id == "sub-123"
    assert event.gateway_subscription_id == "sub_stripe_1"


def test_stripe_gateway_rejects_bad_signature(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    payload = json.dumps({"id": "evt_1", "type": "checkout.session.completed", "data": {"object": {}}}).encode()

    event = StripeGateway().verify_webhook(payload, {"stripe-signature": "t=1,v1=bogus"})
    assert event is None


def _sub_for_talent(db_session, talent_profile):
    return db_session.query(Subscription).filter(Subscription.talent_profile_id == talent_profile["id"]).first()


def test_reactivate_undoes_pending_cancellation(client, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    client.post("/api/v1/billing/cancel", json={"reason_category": "too_expensive"}, headers=talent_headers)

    resp = client.post("/api/v1/billing/reactivate", headers=talent_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cancel_at_period_end"] is False
    assert body["cancellation_reason_category"] is None


def test_reactivate_without_pending_cancellation_400s(client, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    resp = client.post("/api/v1/billing/reactivate", headers=talent_headers)
    assert resp.status_code == 400


def test_retention_offer_available_before_use(client, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    resp = client.get("/api/v1/billing/retention-offer", headers=talent_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["discount_percent"] == settings.RETENTION_DISCOUNT_PERCENT
    assert body["discount_months"] == settings.RETENTION_DISCOUNT_MONTHS


def test_accept_retention_offer_applies_discount_and_clears_cancellation(client, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    client.post("/api/v1/billing/cancel", json={"reason_category": "too_expensive"}, headers=talent_headers)

    resp = client.post("/api/v1/billing/retention-offer/accept", headers=talent_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["discount_percent"] == settings.RETENTION_DISCOUNT_PERCENT
    assert body["discount_expires_at"] is not None
    assert body["cancel_at_period_end"] is False
    assert body["effective_price_lkr"] < body["price_lkr"]

    resp = client.get("/api/v1/billing/retention-offer", headers=talent_headers)
    assert resp.json()["available"] is False


def test_retention_offer_cannot_be_used_twice(client, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    client.post("/api/v1/billing/retention-offer/accept", headers=talent_headers)

    resp = client.post("/api/v1/billing/retention-offer/accept", headers=talent_headers)
    assert resp.status_code == 400


def test_mock_checkout_records_a_payment(client, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    resp = client.get("/api/v1/billing/payments", headers=talent_headers)
    assert resp.status_code == 200
    payments = resp.json()
    assert len(payments) == 1
    assert payments[0]["status"] == "succeeded"
    assert payments[0]["amount_lkr"] == settings.PREMIUM_TALENT_PRICE_LKR


class _FakeRemoteGateway(PaymentGateway):
    """Stands in for Stripe/PayHere in tests — a real remote gateway that doesn't activate the
    subscription until a webhook arrives, unlike the mock gateway used by default in tests.
    """

    name = PaymentGatewayName.STRIPE
    activates_immediately = False

    def __init__(self):
        self.last_trial_days: int | None = None

    def start_checkout(self, subscription, return_url, trial_days: int = 0) -> CheckoutSession:
        self.last_trial_days = trial_days
        return CheckoutSession(redirect_url=f"{return_url}?fake=1", method="get")

    def verify_webhook(self, payload, headers):
        return None

    def cancel(self, subscription):
        pass


def test_remote_gateway_checkout_grants_a_trial_and_waits_for_webhook(client, talent_headers, talent_profile):
    fake_gateway = _FakeRemoteGateway()
    app.dependency_overrides[get_gateway] = lambda: fake_gateway

    resp = client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    assert resp.status_code == 201, resp.text
    assert fake_gateway.last_trial_days == settings.TALENT_TRIAL_DAYS

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    body = resp.json()
    # Checkout only *started* — no webhook has confirmed it yet, so it stays pending.
    assert body["status"] == "pending"
    assert body["trial_end"] is not None

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "free"


def test_remote_gateway_webhook_confirms_trialing_not_active(client, talent_headers, talent_profile, db_session):
    fake_gateway = _FakeRemoteGateway()
    app.dependency_overrides[get_gateway] = lambda: fake_gateway
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    sub_id = client.get("/api/v1/billing/me", headers=talent_headers).json()["id"]
    # checkout.session.completed reports "active" even when a trial_period_days was set —
    # nothing has actually been charged, so this should land as "trialing," not "active".
    subscription_crud.apply_webhook_event(
        db_session, WebhookEvent(status="active", our_subscription_id=sub_id, gateway_subscription_id="gw_sub_1")
    )

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    body = resp.json()
    assert body["status"] == "trialing"
    assert body["trial_end"] is not None

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "premium"

    resp = client.get("/api/v1/billing/payments", headers=talent_headers)
    assert resp.json() == []  # nothing charged yet during the trial


def test_resubscribing_after_confirmed_checkout_gets_no_second_trial(client, talent_headers, talent_profile, db_session):
    fake_gateway = _FakeRemoteGateway()
    app.dependency_overrides[get_gateway] = lambda: fake_gateway
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    sub_id = client.get("/api/v1/billing/me", headers=talent_headers).json()["id"]
    subscription_crud.apply_webhook_event(db_session, WebhookEvent(status="canceled", our_subscription_id=sub_id))

    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    assert fake_gateway.last_trial_days == 0


def test_mock_subscription_auto_renews_past_period_end(client, talent_headers, talent_profile, db_session):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    sub = _sub_for_talent(db_session, talent_profile)
    original_period_end = sub.current_period_end
    sub.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "premium"  # mock gateway auto-renews rather than lapsing

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    body = resp.json()
    assert body["status"] == "active"
    assert body["current_period_end"] != original_period_end.isoformat()

    resp = client.get("/api/v1/billing/payments", headers=talent_headers)
    assert len(resp.json()) == 2  # initial checkout + the simulated renewal


def test_scheduled_cancellation_finalizes_after_period_end(client, talent_headers, talent_profile, db_session):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    client.post("/api/v1/billing/cancel", json={"reason_category": "other"}, headers=talent_headers)

    sub = _sub_for_talent(db_session, talent_profile)
    sub.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "free"

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    assert resp.json()["status"] == "canceled"


def test_past_due_sends_reminder_then_expires(client, talent_headers, talent_profile, db_session):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    sub = _sub_for_talent(db_session, talent_profile)
    sub.status = SubscriptionStatus.PAST_DUE
    sub.past_due_since = datetime.now(timezone.utc) - timedelta(days=settings.PAST_DUE_REMINDER_AFTER_DAYS + 1)
    db_session.commit()

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "premium"  # still within the grace period

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    assert resp.json()["status"] == "past_due"

    db_session.refresh(sub)
    assert sub.past_due_reminder_sent_at is not None

    sub.past_due_since = datetime.now(timezone.utc) - timedelta(days=settings.PAST_DUE_GRACE_DAYS + 1)
    db_session.commit()

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "free"

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    assert resp.json()["status"] == "expired"


def test_admin_can_list_and_filter_subscriptions(client, admin_headers, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    resp = client.get("/api/v1/admin/subscriptions", headers=admin_headers)
    assert resp.status_code == 200
    subs = resp.json()
    assert len(subs) == 1
    assert subs[0]["subscriber_name"] == talent_profile["display_name"]
    assert "@" in subs[0]["subscriber_email"]

    resp = client.get("/api/v1/admin/subscriptions", params={"status_filter": "canceled"}, headers=admin_headers)
    assert resp.json() == []


def test_admin_can_view_subscription_payments(client, admin_headers, talent_headers, talent_profile, db_session):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    sub = _sub_for_talent(db_session, talent_profile)

    resp = client.get(f"/api/v1/admin/subscriptions/{sub.id}/payments", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_admin_churn_reasons_reflects_cancellations(client, admin_headers, talent_headers, talent_profile, db_session):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    client.post("/api/v1/billing/cancel", json={"reason_category": "too_expensive", "reason_detail": "can't afford it"}, headers=talent_headers)

    sub = _sub_for_talent(db_session, talent_profile)
    sub.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()
    client.get("/api/v1/talents/me", headers=talent_headers)  # triggers the lazy finalize

    resp = client.get("/api/v1/admin/churn-reasons", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["counts"]["too_expensive"] == 1
    assert "can't afford it" in body["recent_details"]


def test_admin_dunning_sweep_endpoint(client, admin_headers, talent_headers, talent_profile, db_session):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)
    sub = _sub_for_talent(db_session, talent_profile)
    sub.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    resp = client.post("/api/v1/admin/billing/run-dunning-sweep", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["checked"] >= 1
    assert body["transitions_applied"] >= 1

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "premium"  # the sweep already auto-renewed the mock subscription


def test_non_admin_cannot_access_billing_admin_routes(client, talent_headers):
    assert client.get("/api/v1/admin/subscriptions", headers=talent_headers).status_code == 403
    assert client.get("/api/v1/admin/churn-reasons", headers=talent_headers).status_code == 403
    assert client.post("/api/v1/admin/billing/run-dunning-sweep", headers=talent_headers).status_code == 403

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.payments.payhere import PayHereGateway
from app.core.payments.stripe_gateway import StripeGateway
from app.models.subscription import Subscription


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


def test_cancel_reverts_to_free(client, talent_headers, talent_profile):
    client.post("/api/v1/billing/checkout", json={"billing_cycle": "monthly"}, headers=talent_headers)

    resp = client.post("/api/v1/billing/cancel", headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "canceled"

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "free"


def test_cancel_without_a_subscription_404s(client, talent_headers, talent_profile):
    resp = client.post("/api/v1/billing/cancel", headers=talent_headers)
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

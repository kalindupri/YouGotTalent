from app.core.config import settings
from tests.conftest import auth_headers, register_and_verify


def test_public_pricing_defaults_match_settings_when_no_versions_exist(client):
    resp = client.get("/api/v1/billing/pricing")
    assert resp.status_code == 200
    body = resp.json()
    assert body["talent_premium_monthly_lkr"] == settings.PREMIUM_TALENT_PRICE_LKR
    assert body["recruiter_premium_monthly_lkr"] == settings.PREMIUM_RECRUITER_PRICE_LKR
    assert body["talent_premium_annual_lkr"] == settings.PREMIUM_TALENT_PRICE_LKR * settings.ANNUAL_BILLING_MONTHS_CHARGED


def test_non_admin_cannot_view_or_update_pricing(client, talent_headers, talent_profile):
    assert client.get("/api/v1/admin/pricing", headers=talent_headers).status_code == 403
    resp = client.post(
        "/api/v1/admin/pricing",
        json={"plan": "talent_premium", "monthly_price_lkr": 999},
        headers=talent_headers,
    )
    assert resp.status_code == 403


def test_admin_setting_a_new_price_is_reflected_publicly(client, admin_headers):
    resp = client.post(
        "/api/v1/admin/pricing",
        json={"plan": "talent_premium", "monthly_price_lkr": 650},
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["current"]["talent_premium_monthly_lkr"] == 650

    resp = client.get("/api/v1/billing/pricing")
    assert resp.json()["talent_premium_monthly_lkr"] == 650
    assert resp.json()["talent_premium_annual_lkr"] == 650 * settings.ANNUAL_BILLING_MONTHS_CHARGED
    # Untouched plan keeps its settings-derived default.
    assert resp.json()["recruiter_premium_monthly_lkr"] == settings.PREMIUM_RECRUITER_PRICE_LKR


def test_price_change_does_not_affect_an_existing_subscription(client, talent_headers, talent_profile, admin_headers):
    resp = client.post("/api/v1/talents/me/upgrade", headers=talent_headers)
    assert resp.status_code == 200
    original_price = client.get("/api/v1/billing/me", headers=talent_headers).json()["price_lkr"]
    assert original_price == settings.PREMIUM_TALENT_PRICE_LKR

    client.post(
        "/api/v1/admin/pricing",
        json={"plan": "talent_premium", "monthly_price_lkr": 999},
        headers=admin_headers,
    )

    resp = client.get("/api/v1/billing/me", headers=talent_headers)
    assert resp.json()["price_lkr"] == original_price
    assert resp.json()["price_lkr"] != 999


def test_new_signup_after_price_change_gets_the_new_price(client, db_session, admin_headers):
    client.post(
        "/api/v1/admin/pricing",
        json={"plan": "talent_premium", "monthly_price_lkr": 777},
        headers=admin_headers,
    )

    new_token = register_and_verify(client, db_session, "pricing_new_talent@example.com", full_name="New Talent", role="talent")
    new_headers = auth_headers(new_token)
    resp = client.post(
        "/api/v1/talents/me",
        json={"display_name": "New Talent", "category": "acting", "city": "Colombo"},
        headers=new_headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.post("/api/v1/talents/me/upgrade", headers=new_headers)
    assert resp.status_code == 200

    resp = client.get("/api/v1/billing/me", headers=new_headers)
    assert resp.json()["price_lkr"] == 777


def test_pricing_history_lists_newest_first_with_admin_attribution(client, admin_headers):
    client.post("/api/v1/admin/pricing", json={"plan": "talent_premium", "monthly_price_lkr": 500}, headers=admin_headers)
    client.post("/api/v1/admin/pricing", json={"plan": "talent_premium", "monthly_price_lkr": 550}, headers=admin_headers)

    resp = client.get("/api/v1/admin/pricing", headers=admin_headers)
    assert resp.status_code == 200
    history = [v for v in resp.json()["history"] if v["plan"] == "talent_premium"]
    assert history[0]["monthly_price_lkr"] == 550
    assert history[1]["monthly_price_lkr"] == 500
    assert history[0]["created_by_name"] is not None


def test_pricing_rejects_non_positive_price(client, admin_headers):
    resp = client.post("/api/v1/admin/pricing", json={"plan": "talent_premium", "monthly_price_lkr": 0}, headers=admin_headers)
    assert resp.status_code == 422

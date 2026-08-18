from tests.conftest import ADULT_DOB, DEFAULT_PASSWORD


def test_register_rejects_admin_role(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "wannabe-admin@example.com",
            "password": DEFAULT_PASSWORD,
            "full_name": "Wannabe Admin",
            "role": "admin",
            "consent_given": True,
        },
    )
    assert resp.status_code == 422


def test_admin_endpoints_require_authentication(client):
    resp = client.get("/api/v1/admin/stats")
    assert resp.status_code == 401


def test_admin_endpoints_reject_talent(client, talent_headers):
    resp = client.get("/api/v1/admin/stats", headers=talent_headers)
    assert resp.status_code == 403


def test_admin_endpoints_reject_recruiter(client, recruiter_headers):
    resp = client.get("/api/v1/admin/stats", headers=recruiter_headers)
    assert resp.status_code == 403


def test_stats_reflect_platform_state(client, admin_headers, talent_headers, recruiter_headers, recruiter_profile):
    client.post("/api/v1/talents/me", json={"date_of_birth": ADULT_DOB, "display_name": "Stats Talent", "category": "acting"}, headers=talent_headers)
    call = client.post(
        "/api/v1/casting-calls",
        json={"title": "Stats call", "description": "x", "category": "acting", "roles": [{"title": "x"}]},
        headers=recruiter_headers,
    ).json()

    resp = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_users"] == 3  # talent + recruiter + admin
    assert body["total_talents"] == 1
    assert body["total_recruiters"] == 1
    assert body["open_casting_calls"] == 1
    assert body["closed_casting_calls"] == 0
    assert call["status"] == "open"


def test_list_users_filters_by_role(client, admin_headers, talent_headers, recruiter_headers):
    resp = client.get("/api/v1/admin/users", params={"role": "talent"}, headers=admin_headers)
    assert resp.status_code == 200
    roles = {u["role"] for u in resp.json()}
    assert roles == {"talent"}


def test_list_users_search_by_email(client, admin_headers, talent_headers):
    resp = client.get("/api/v1/admin/users", params={"q": "talent_fixture"}, headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["email"] == "talent_fixture@example.com"


def test_suspend_and_reactivate_user(client, db_session, admin_headers, talent_headers):
    from app.models.user import User

    talent_user = db_session.query(User).filter(User.email == "talent_fixture@example.com").first()

    resp = client.patch(
        f"/api/v1/admin/users/{talent_user.id}/status", json={"is_active": False}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "talent_fixture@example.com", "password": DEFAULT_PASSWORD},
    )
    assert resp.status_code == 403
    assert "suspended" in resp.json()["detail"].lower()

    resp = client.patch(
        f"/api/v1/admin/users/{talent_user.id}/status", json={"is_active": True}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True

    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "talent_fixture@example.com", "password": DEFAULT_PASSWORD},
    )
    assert resp.status_code == 200


def test_admin_cannot_suspend_own_account(client, db_session, admin_headers):
    from app.models.user import User

    admin_user = db_session.query(User).filter(User.email == "admin_fixture@example.com").first()
    resp = client.patch(
        f"/api/v1/admin/users/{admin_user.id}/status", json={"is_active": False}, headers=admin_headers
    )
    assert resp.status_code == 400


def test_suspend_unknown_user_404(client, admin_headers):
    resp = client.patch(
        "/api/v1/admin/users/00000000-0000-0000-0000-000000000000/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 404


def test_talent_verification_approve_flow(client, admin_headers, talent_headers):
    client.post("/api/v1/talents/me", json={"date_of_birth": ADULT_DOB, "display_name": "Verify Me", "category": "acting"}, headers=talent_headers)
    talent = client.get("/api/v1/talents/me", headers=talent_headers).json()
    client.post("/api/v1/talents/me/request-verification", headers=talent_headers)

    resp = client.get("/api/v1/admin/verification-requests/talents", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == talent["id"]

    resp = client.post(f"/api/v1/admin/verification-requests/talents/{talent['id']}/approve", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_verified"] is True
    assert resp.json()["verification_requested_at"] is None

    resp = client.get("/api/v1/admin/verification-requests/talents", headers=admin_headers)
    assert resp.json() == []


def test_talent_verification_reject_flow(client, admin_headers, talent_headers):
    client.post("/api/v1/talents/me", json={"date_of_birth": ADULT_DOB, "display_name": "Reject Me", "category": "acting"}, headers=talent_headers)
    talent = client.get("/api/v1/talents/me", headers=talent_headers).json()
    client.post("/api/v1/talents/me/request-verification", headers=talent_headers)

    resp = client.post(f"/api/v1/admin/verification-requests/talents/{talent['id']}/reject", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_verified"] is False
    assert resp.json()["verification_requested_at"] is None

    resp = client.get("/api/v1/admin/verification-requests/talents", headers=admin_headers)
    assert resp.json() == []


def test_recruiter_verification_approve_flow(client, admin_headers, recruiter_headers, recruiter_profile):
    client.post("/api/v1/recruiters/me/request-verification", headers=recruiter_headers)

    resp = client.get("/api/v1/admin/verification-requests/recruiters", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.post(
        f"/api/v1/admin/verification-requests/recruiters/{recruiter_profile['id']}/approve", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["is_verified"] is True


def test_casting_call_moderation_close_and_reopen(client, admin_headers, recruiter_headers, casting_call):
    resp = client.patch(
        f"/api/v1/admin/casting-calls/{casting_call['id']}/status",
        json={"status": "closed"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"

    resp = client.get("/api/v1/admin/casting-calls", params={"status_filter": "closed"}, headers=admin_headers)
    assert len(resp.json()) == 1

    resp = client.patch(
        f"/api/v1/admin/casting-calls/{casting_call['id']}/status",
        json={"status": "open"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "open"


def test_casting_call_admin_detail_includes_recruiter_and_counts(
    client, admin_headers, talent_headers, recruiter_headers, recruiter_profile, casting_call
):
    client.post("/api/v1/talents/me", json={"date_of_birth": ADULT_DOB, "display_name": "Applicant", "category": "acting"}, headers=talent_headers)
    role_id = casting_call["roles"][0]["id"]
    client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id},
        headers=talent_headers,
    )

    resp = client.get("/api/v1/admin/casting-calls", headers=admin_headers)
    assert resp.status_code == 200
    body = next(c for c in resp.json() if c["id"] == casting_call["id"])
    assert body["recruiter_company_name"] == recruiter_profile["company_name"]
    assert body["application_count"] == 1
    assert body["invitation_count"] == 0
    assert body["description"] == casting_call["description"]
    assert len(body["roles"]) == 1


def test_financial_overview_reflects_tiers(client, admin_headers, talent_headers, recruiter_headers, recruiter_profile):
    from app.core.config import settings

    client.post("/api/v1/talents/me", json={"date_of_birth": ADULT_DOB, "display_name": "Fin Talent", "category": "acting"}, headers=talent_headers)
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)

    resp = client.get("/api/v1/admin/financial-overview", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["currency"] == "LKR"
    assert body["premium_talents"] == 1
    assert body["free_talents"] == 0
    assert body["premium_recruiters"] == 0
    assert body["free_recruiters"] == 1
    assert body["price_per_premium_talent"] == settings.PREMIUM_TALENT_PRICE_LKR
    assert body["estimated_monthly_revenue"] == settings.PREMIUM_TALENT_PRICE_LKR


def test_admin_endpoints_reject_non_admin_for_new_routes(client, talent_headers):
    assert client.get("/api/v1/admin/financial-overview", headers=talent_headers).status_code == 403
    assert client.get("/api/v1/admin/casting-calls", headers=talent_headers).status_code == 403


def test_user_detail_includes_talent_profile(client, admin_headers, talent_headers, db_session):
    from app.models.user import User

    client.post("/api/v1/talents/me", json={"date_of_birth": ADULT_DOB, "display_name": "Detail Talent", "category": "singing"}, headers=talent_headers)
    talent_user = db_session.query(User).filter(User.email == "talent_fixture@example.com").first()

    resp = client.get(f"/api/v1/admin/users/{talent_user.id}", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "talent_fixture@example.com"
    assert [p["display_name"] for p in body["talent_profiles"]] == ["Detail Talent"]
    assert body["recruiter_profile"] is None


def test_user_detail_includes_recruiter_profile(client, admin_headers, recruiter_headers, recruiter_profile, db_session):
    from app.models.user import User

    recruiter_user = db_session.query(User).filter(User.email == "recruiter_fixture@example.com").first()

    resp = client.get(f"/api/v1/admin/users/{recruiter_user.id}", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["recruiter_profile"]["company_name"] == recruiter_profile["company_name"]
    assert body["talent_profiles"] == []


def test_user_detail_with_no_profile_returns_nulls(client, admin_headers, db_session):
    from tests.conftest import register_and_verify

    token = register_and_verify(client, db_session, "no-profile@example.com", role="talent")
    from app.models.user import User

    user = db_session.query(User).filter(User.email == "no-profile@example.com").first()

    resp = client.get(f"/api/v1/admin/users/{user.id}", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["talent_profiles"] == []
    assert body["recruiter_profile"] is None
    assert token  # unused otherwise; keeps the fixture call meaningful


def test_user_detail_unknown_user_404(client, admin_headers):
    resp = client.get("/api/v1/admin/users/00000000-0000-0000-0000-000000000000", headers=admin_headers)
    assert resp.status_code == 404

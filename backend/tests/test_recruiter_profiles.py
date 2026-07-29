def test_create_recruiter_profile(client, recruiter_headers):
    resp = client.post(
        "/api/v1/recruiters/me",
        json={"company_name": "Panthera Model Management", "industry": "Fashion"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["company_name"] == "Panthera Model Management"
    assert body["tier"] == "free"
    assert body["is_verified"] is False


def test_create_recruiter_profile_twice_rejected(client, recruiter_headers):
    client.post("/api/v1/recruiters/me", json={"company_name": "First"}, headers=recruiter_headers)
    resp = client.post("/api/v1/recruiters/me", json={"company_name": "Second"}, headers=recruiter_headers)
    assert resp.status_code == 400


def test_create_recruiter_profile_requires_recruiter_role(client, talent_headers):
    resp = client.post("/api/v1/recruiters/me", json={"company_name": "Wrong role"}, headers=talent_headers)
    assert resp.status_code == 403


def test_read_my_recruiter_profile_404_before_creation(client, recruiter_headers):
    resp = client.get("/api/v1/recruiters/me", headers=recruiter_headers)
    assert resp.status_code == 404


def test_read_my_recruiter_profile(client, recruiter_headers):
    client.post("/api/v1/recruiters/me", json={"company_name": "Studio"}, headers=recruiter_headers)
    resp = client.get("/api/v1/recruiters/me", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json()["company_name"] == "Studio"


def test_request_verification(client, recruiter_headers):
    client.post("/api/v1/recruiters/me", json={"company_name": "Studio"}, headers=recruiter_headers)
    resp = client.post("/api/v1/recruiters/me/request-verification", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json()["verification_requested_at"] is not None


def test_upgrade_tier(client, recruiter_headers):
    client.post("/api/v1/recruiters/me", json={"company_name": "Studio"}, headers=recruiter_headers)
    resp = client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json()["tier"] == "premium"


def test_saved_searches_require_premium(client, recruiter_headers):
    client.post("/api/v1/recruiters/me", json={"company_name": "Studio"}, headers=recruiter_headers)
    resp = client.post(
        "/api/v1/recruiters/me/saved-searches",
        json={"name": "My search", "category": "modeling"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 403
    assert "premium" in resp.json()["detail"].lower()


def test_saved_search_lifecycle_for_premium_recruiter(client, recruiter_headers):
    client.post("/api/v1/recruiters/me", json={"company_name": "Studio"}, headers=recruiter_headers)
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)

    resp = client.post(
        "/api/v1/recruiters/me/saved-searches",
        json={"name": "Colombo models", "category": "modeling", "city": "Colombo", "verified_only": True},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    saved_id = resp.json()["id"]

    resp = client.get("/api/v1/recruiters/me/saved-searches", headers=recruiter_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.delete(f"/api/v1/recruiters/me/saved-searches/{saved_id}", headers=recruiter_headers)
    assert resp.status_code == 204

    resp = client.get("/api/v1/recruiters/me/saved-searches", headers=recruiter_headers)
    assert resp.json() == []


def test_cannot_delete_another_recruiters_saved_search(client, db_session):
    from tests.conftest import register_and_verify, auth_headers

    token_a = register_and_verify(client, db_session, "recruiter-a@example.com", role="recruiter")
    token_b = register_and_verify(client, db_session, "recruiter-b@example.com", role="recruiter")
    headers_a = auth_headers(token_a)
    headers_b = auth_headers(token_b)

    client.post("/api/v1/recruiters/me", json={"company_name": "A Co"}, headers=headers_a)
    client.post("/api/v1/recruiters/me/upgrade", headers=headers_a)
    client.post("/api/v1/recruiters/me", json={"company_name": "B Co"}, headers=headers_b)

    resp = client.post(
        "/api/v1/recruiters/me/saved-searches", json={"name": "A's search"}, headers=headers_a
    )
    saved_id = resp.json()["id"]

    resp = client.delete(f"/api/v1/recruiters/me/saved-searches/{saved_id}", headers=headers_b)
    assert resp.status_code == 404

from tests.conftest import auth_headers, register_and_verify


def create_talent_profile(client, headers, **overrides):
    payload = {"display_name": "New Arrival", "category": "acting"}
    payload.update(overrides)
    resp = client.post("/api/v1/talents/me", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_free_recruiter_cannot_see_new_arrivals(client, recruiter_headers, recruiter_profile):
    resp = client.get("/api/v1/recruiters/me/new-arrivals", headers=recruiter_headers)
    assert resp.status_code == 403


def test_premium_recruiter_sees_new_talent_in_their_posted_categories(
    client, recruiter_headers, recruiter_profile, talent_headers, db_session
):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    client.post(
        "/api/v1/casting-calls",
        json={"title": "Lead role", "description": "x", "category": "acting", "roles": [{"title": "Lead role"}]},
        headers=recruiter_headers,
    )
    create_talent_profile(client, talent_headers, category="acting")

    other_token = register_and_verify(client, db_session, "unrelated-category@example.com", role="talent")
    other_headers = auth_headers(other_token)
    create_talent_profile(client, other_headers, display_name="Painter", category="painting")

    resp = client.get("/api/v1/recruiters/me/new-arrivals", headers=recruiter_headers)
    assert resp.status_code == 200
    body = resp.json()
    categories = {t["category"] for t in body}
    assert categories == {"acting"}


def test_premium_recruiter_with_no_casting_calls_sees_no_arrivals(client, recruiter_headers, recruiter_profile, talent_headers):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    create_talent_profile(client, talent_headers, category="acting")

    resp = client.get("/api/v1/recruiters/me/new-arrivals", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json() == []

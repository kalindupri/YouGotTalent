from tests.conftest import ADULT_DOB, auth_headers, register_and_verify


def create_talent_profile(client, headers, **overrides):
    payload = {"date_of_birth": ADULT_DOB, "display_name": "New Arrival", "category": "acting"}
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


def test_new_arrival_matched_by_secondary_category(client, recruiter_headers, recruiter_profile, talent_headers):
    # Primary category is acting, but painting is a secondary category — a painting-only
    # casting call must still surface this talent in the new-arrivals feed.
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    client.post(
        "/api/v1/casting-calls",
        json={"title": "Mural project", "description": "x", "category": "painting", "roles": [{"title": "Mural project"}]},
        headers=recruiter_headers,
    )
    create_talent_profile(client, talent_headers, categories=["acting", "painting"])

    resp = client.get("/api/v1/recruiters/me/new-arrivals", headers=recruiter_headers)
    assert resp.status_code == 200
    names = {t["display_name"] for t in resp.json()}
    assert "New Arrival" in names


def test_premium_recruiter_with_no_casting_calls_sees_no_arrivals(client, recruiter_headers, recruiter_profile, talent_headers):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    create_talent_profile(client, talent_headers, category="acting")

    resp = client.get("/api/v1/recruiters/me/new-arrivals", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json() == []

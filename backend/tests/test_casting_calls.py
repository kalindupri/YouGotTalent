from tests.conftest import auth_headers, register_and_verify


def test_create_single_role_casting_call(client, recruiter_headers, recruiter_profile):
    resp = client.post(
        "/api/v1/casting-calls",
        json={
            "title": "Lead vocalist for ad jingle",
            "description": "Need a versatile singer for a 30-second jingle",
            "category": "singing",
            "location": "Colombo",
            "roles": [{"title": "Lead vocalist for ad jingle"}],
        },
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "Lead vocalist for ad jingle"
    assert body["status"] == "open"
    assert len(body["roles"]) == 1
    assert body["roles"][0]["title"] == "Lead vocalist for ad jingle"


def test_create_multi_role_casting_call(client, recruiter_headers, recruiter_profile):
    resp = client.post(
        "/api/v1/casting-calls",
        json={
            "title": "K Republiq Skincare UGC/B-roll",
            "description": "Seeking women of all ages to create UGC content.",
            "category": "modeling",
            "location": "Worldwide",
            "tags": ["Product Demo / Explainer Video"],
            "shoot_details": "Shoots remotely at home.",
            "roles": [
                {"title": "Content creators", "criteria": "Female, 18+", "category": "other", "compensation": "AU$150"},
                {"title": "Models", "criteria": "Female, 18+", "category": "modeling"},
                {"title": "Actors/Performers", "criteria": "Lead, Female, 18+", "category": "acting"},
            ],
        },
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert len(body["roles"]) == 3
    titles = {r["title"] for r in body["roles"]}
    assert titles == {"Content creators", "Models", "Actors/Performers"}
    assert body["tags"] == ["Product Demo / Explainer Video"]
    assert body["shoot_details"] == "Shoots remotely at home."


def test_create_casting_call_requires_at_least_one_role(client, recruiter_headers, recruiter_profile):
    resp = client.post(
        "/api/v1/casting-calls",
        json={"title": "No roles", "description": "x", "category": "acting", "roles": []},
        headers=recruiter_headers,
    )
    assert resp.status_code == 422


def test_create_casting_call_requires_recruiter_role(client, talent_headers):
    resp = client.post(
        "/api/v1/casting-calls",
        json={"title": "x", "description": "x", "category": "acting", "roles": [{"title": "x"}]},
        headers=talent_headers,
    )
    assert resp.status_code == 403


def test_free_tier_open_casting_call_limit(client, recruiter_headers, recruiter_profile):
    for i in range(2):
        resp = client.post(
            "/api/v1/casting-calls",
            json={"title": f"Call {i}", "description": "x", "category": "acting", "roles": [{"title": f"Call {i}"}]},
            headers=recruiter_headers,
        )
        assert resp.status_code == 201, resp.text

    resp = client.post(
        "/api/v1/casting-calls",
        json={"title": "Call 3", "description": "x", "category": "acting", "roles": [{"title": "Call 3"}]},
        headers=recruiter_headers,
    )
    assert resp.status_code == 403
    assert "premium" in resp.json()["detail"].lower()


def test_premium_recruiter_bypasses_open_call_limit(client, recruiter_headers, recruiter_profile):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    for i in range(4):
        resp = client.post(
            "/api/v1/casting-calls",
            json={"title": f"Call {i}", "description": "x", "category": "acting", "roles": [{"title": f"Call {i}"}]},
            headers=recruiter_headers,
        )
        assert resp.status_code == 201, resp.text


def test_is_featured_reflects_recruiter_tier(client, recruiter_headers, recruiter_profile):
    resp = client.post(
        "/api/v1/casting-calls",
        json={"title": "Free tier call", "description": "x", "category": "acting", "roles": [{"title": "x"}]},
        headers=recruiter_headers,
    )
    assert resp.json()["is_featured"] is False

    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    resp = client.post(
        "/api/v1/casting-calls",
        json={"title": "Premium tier call", "description": "x", "category": "acting", "roles": [{"title": "x"}]},
        headers=recruiter_headers,
    )
    assert resp.json()["is_featured"] is True


def test_browse_casting_calls_filter_by_category(client, casting_call, recruiter_headers):
    client.post(
        "/api/v1/casting-calls",
        json={"title": "Modeling call", "description": "x", "category": "modeling", "roles": [{"title": "x"}]},
        headers=recruiter_headers,
    )

    resp = client.get("/api/v1/casting-calls", params={"category": "modeling"})
    assert resp.status_code == 200
    categories = {c["category"] for c in resp.json()}
    assert categories == {"modeling"}


def test_get_casting_call_by_id(client, casting_call):
    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == casting_call["id"]


def test_get_casting_call_unknown_id_404(client):
    resp = client.get("/api/v1/casting-calls/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_owner_can_update_own_casting_call(client, casting_call, recruiter_headers):
    resp = client.patch(
        f"/api/v1/casting-calls/{casting_call['id']}",
        json={"title": "Updated title", "compensation": "LKR 50,000", "status": "closed"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["title"] == "Updated title"
    assert body["compensation"] == "LKR 50,000"
    assert body["status"] == "closed"
    # Untouched fields survive a partial update.
    assert body["description"] == casting_call["description"]


def test_owner_can_delete_own_casting_call(client, casting_call, recruiter_headers):
    resp = client.delete(f"/api/v1/casting-calls/{casting_call['id']}", headers=recruiter_headers)
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}")
    assert resp.status_code == 404


def test_non_owner_cannot_update_or_delete_casting_call(client, casting_call, db_session):
    other_token = register_and_verify(client, db_session, "other-recruiter@example.com", role="recruiter")
    other_headers = auth_headers(other_token)
    client.post(
        "/api/v1/recruiters/me",
        json={"company_name": "Other Agency", "industry": "Film"},
        headers=other_headers,
    )

    resp = client.patch(f"/api/v1/casting-calls/{casting_call['id']}", json={"title": "Hijacked"}, headers=other_headers)
    assert resp.status_code == 403

    resp = client.delete(f"/api/v1/casting-calls/{casting_call['id']}", headers=other_headers)
    assert resp.status_code == 403

    # Still there, untouched.
    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == casting_call["title"]


def test_update_unknown_casting_call_404(client, recruiter_headers):
    resp = client.patch(
        "/api/v1/casting-calls/00000000-0000-0000-0000-000000000000",
        json={"title": "x"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 404

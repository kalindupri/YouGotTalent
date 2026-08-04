def create_talent_profile(client, headers, **overrides):
    payload = {"display_name": "Fixture Talent", "category": "acting", "city": "Colombo"}
    payload.update(overrides)
    resp = client.post("/api/v1/talents/me", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_anonymous_view_not_recorded(client, talent_headers):
    talent = create_talent_profile(client, talent_headers)
    client.get(f"/api/v1/talents/{talent['id']}")

    resp = client.get("/api/v1/talents/me/profile-views", headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_recruiter_viewing_profile_is_recorded(client, talent_headers, recruiter_headers, recruiter_profile):
    talent = create_talent_profile(client, talent_headers)
    client.get(f"/api/v1/talents/{talent['id']}", headers=recruiter_headers)

    resp = client.get("/api/v1/talents/me/profile-views", headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


def test_free_talent_sees_count_but_not_viewer_identities(client, talent_headers, recruiter_headers, recruiter_profile):
    talent = create_talent_profile(client, talent_headers)
    client.get(f"/api/v1/talents/{talent['id']}", headers=recruiter_headers)

    resp = client.get("/api/v1/talents/me/profile-views", headers=talent_headers)
    body = resp.json()
    assert body["count"] == 1
    assert body["viewers"] == []


def test_premium_talent_sees_viewer_identities(client, talent_headers, recruiter_headers, recruiter_profile):
    talent = create_talent_profile(client, talent_headers)
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)
    client.get(f"/api/v1/talents/{talent['id']}", headers=recruiter_headers)

    resp = client.get("/api/v1/talents/me/profile-views", headers=talent_headers)
    body = resp.json()
    assert body["count"] == 1
    assert len(body["viewers"]) == 1
    assert body["viewers"][0]["company_name"] == recruiter_profile["company_name"]


def test_repeat_views_from_same_recruiter_count_every_visit_but_dedupe_in_viewers_list(
    client, talent_headers, recruiter_headers, recruiter_profile
):
    talent = create_talent_profile(client, talent_headers)
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)
    client.get(f"/api/v1/talents/{talent['id']}", headers=recruiter_headers)
    client.get(f"/api/v1/talents/{talent['id']}", headers=recruiter_headers)

    resp = client.get("/api/v1/talents/me/profile-views", headers=talent_headers)
    body = resp.json()
    assert body["count"] == 2
    assert len(body["viewers"]) == 1

def create_talent(client, talent_headers, **overrides):
    payload = {"display_name": "Nadeesha P.", "category": "modeling"}
    payload.update(overrides)
    return client.post("/api/v1/talents/me", json=payload, headers=talent_headers).json()


def test_save_and_list_talent(client, recruiter_headers, recruiter_profile, talent_headers):
    talent = create_talent(client, talent_headers)
    resp = client.post(f"/api/v1/talents/{talent['id']}/save", headers=recruiter_headers)
    assert resp.status_code == 204

    resp = client.get("/api/v1/recruiters/me/saved-talents", headers=recruiter_headers)
    assert resp.status_code == 200
    assert [t["id"] for t in resp.json()] == [talent["id"]]


def test_saving_same_talent_twice_is_idempotent(client, recruiter_headers, recruiter_profile, talent_headers):
    talent = create_talent(client, talent_headers)
    client.post(f"/api/v1/talents/{talent['id']}/save", headers=recruiter_headers)
    resp = client.post(f"/api/v1/talents/{talent['id']}/save", headers=recruiter_headers)
    assert resp.status_code == 204

    resp = client.get("/api/v1/recruiters/me/saved-talents", headers=recruiter_headers)
    assert len(resp.json()) == 1


def test_unsave_talent(client, recruiter_headers, recruiter_profile, talent_headers):
    talent = create_talent(client, talent_headers)
    client.post(f"/api/v1/talents/{talent['id']}/save", headers=recruiter_headers)

    resp = client.delete(f"/api/v1/talents/{talent['id']}/save", headers=recruiter_headers)
    assert resp.status_code == 204

    resp = client.get("/api/v1/recruiters/me/saved-talents", headers=recruiter_headers)
    assert resp.json() == []


def test_unsave_when_not_saved_is_a_no_op(client, recruiter_headers, recruiter_profile, talent_headers):
    talent = create_talent(client, talent_headers)
    resp = client.delete(f"/api/v1/talents/{talent['id']}/save", headers=recruiter_headers)
    assert resp.status_code == 204


def test_save_requires_recruiter_role(client, talent_headers):
    other = create_talent(client, talent_headers)
    resp = client.post(f"/api/v1/talents/{other['id']}/save", headers=talent_headers)
    assert resp.status_code == 403


def test_save_unknown_talent_404(client, recruiter_headers, recruiter_profile):
    resp = client.post(
        "/api/v1/talents/00000000-0000-0000-0000-000000000000/save", headers=recruiter_headers
    )
    assert resp.status_code == 404

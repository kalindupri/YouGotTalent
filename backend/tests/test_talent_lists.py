from tests.conftest import ADULT_DOB, auth_headers, register_and_verify


def create_talent_profile(client, headers, **overrides):
    payload = {"date_of_birth": ADULT_DOB, "display_name": "Listed Talent", "category": "acting"}
    payload.update(overrides)
    resp = client.post("/api/v1/talents/me", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_free_recruiter_cannot_create_talent_list(client, recruiter_headers, recruiter_profile):
    resp = client.post("/api/v1/recruiters/me/talent-lists", json={"name": "Leads"}, headers=recruiter_headers)
    assert resp.status_code == 403


def test_premium_recruiter_creates_and_lists_talent_lists(client, recruiter_headers, recruiter_profile):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    resp = client.post("/api/v1/recruiters/me/talent-lists", json={"name": "Leads"}, headers=recruiter_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["name"] == "Leads"
    assert resp.json()["members"] == []

    resp = client.get("/api/v1/recruiters/me/talent-lists", headers=recruiter_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_add_update_and_remove_list_member(client, recruiter_headers, recruiter_profile, talent_headers):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    talent = create_talent_profile(client, talent_headers)
    talent_list = client.post("/api/v1/recruiters/me/talent-lists", json={"name": "Leads"}, headers=recruiter_headers).json()

    resp = client.post(
        f"/api/v1/recruiters/me/talent-lists/{talent_list['id']}/members",
        json={"talent_id": talent["id"], "notes": "Great reel"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    member = resp.json()
    assert member["talent_display_name"] == talent["display_name"]
    assert member["notes"] == "Great reel"

    resp = client.patch(
        f"/api/v1/recruiters/me/talent-lists/{talent_list['id']}/members/{member['id']}",
        json={"notes": "Callback scheduled"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Callback scheduled"

    resp = client.delete(
        f"/api/v1/recruiters/me/talent-lists/{talent_list['id']}/members/{member['id']}", headers=recruiter_headers
    )
    assert resp.status_code == 204

    resp = client.get("/api/v1/recruiters/me/talent-lists", headers=recruiter_headers)
    assert resp.json()[0]["members"] == []


def test_cannot_add_same_talent_to_list_twice(client, recruiter_headers, recruiter_profile, talent_headers):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    talent = create_talent_profile(client, talent_headers)
    talent_list = client.post("/api/v1/recruiters/me/talent-lists", json={"name": "Leads"}, headers=recruiter_headers).json()

    payload = {"talent_id": talent["id"]}
    resp1 = client.post(f"/api/v1/recruiters/me/talent-lists/{talent_list['id']}/members", json=payload, headers=recruiter_headers)
    assert resp1.status_code == 201
    resp2 = client.post(f"/api/v1/recruiters/me/talent-lists/{talent_list['id']}/members", json=payload, headers=recruiter_headers)
    assert resp2.status_code == 400


def test_other_recruiter_cannot_see_or_modify_list(client, recruiter_headers, recruiter_profile, db_session):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    talent_list = client.post("/api/v1/recruiters/me/talent-lists", json={"name": "Leads"}, headers=recruiter_headers).json()

    other_token = register_and_verify(client, db_session, "other-list-recruiter@example.com", role="recruiter")
    other_headers = auth_headers(other_token)
    client.post("/api/v1/recruiters/me", json={"company_name": "Other Co"}, headers=other_headers)
    client.post("/api/v1/recruiters/me/upgrade", headers=other_headers)

    resp = client.delete(f"/api/v1/recruiters/me/talent-lists/{talent_list['id']}", headers=other_headers)
    assert resp.status_code == 404

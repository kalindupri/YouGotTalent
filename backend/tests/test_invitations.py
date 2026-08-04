from tests.conftest import register_and_verify, auth_headers


def create_talent_profile(client, headers, **overrides):
    payload = {"display_name": "Invitee", "category": "acting"}
    payload.update(overrides)
    resp = client.post("/api/v1/talents/me", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_recruiter_invites_talent(client, recruiter_headers, talent_headers, casting_call):
    talent = create_talent_profile(client, talent_headers)
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": talent["id"], "message": "Loved your reel"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["talent_id"] == talent["id"]
    assert body["status"] == "pending"
    assert body["message"] == "Loved your reel"
    assert body["casting_call"]["id"] == casting_call["id"]


def test_invite_requires_recruiter_role(client, talent_headers, casting_call):
    other_talent = create_talent_profile(client, talent_headers)
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": other_talent["id"]},
        headers=talent_headers,
    )
    assert resp.status_code == 403


def test_invite_to_call_owned_by_someone_else_404(client, talent_headers, casting_call, db_session):
    talent = create_talent_profile(client, talent_headers)
    other_token = register_and_verify(client, db_session, "othercall@example.com", role="recruiter")
    other_headers = auth_headers(other_token)
    client.post("/api/v1/recruiters/me", json={"company_name": "Other"}, headers=other_headers)

    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": talent["id"]},
        headers=other_headers,
    )
    assert resp.status_code == 404


def test_invite_unknown_talent_404(client, recruiter_headers, casting_call):
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": "00000000-0000-0000-0000-000000000000"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 404


def test_duplicate_invite_rejected(client, recruiter_headers, talent_headers, casting_call):
    talent = create_talent_profile(client, talent_headers)
    payload = {"talent_id": talent["id"]}
    resp1 = client.post(f"/api/v1/casting-calls/{casting_call['id']}/invitations", json=payload, headers=recruiter_headers)
    assert resp1.status_code == 201
    resp2 = client.post(f"/api/v1/casting-calls/{casting_call['id']}/invitations", json=payload, headers=recruiter_headers)
    assert resp2.status_code == 400


def test_free_recruiter_cannot_bulk_invite_more_than_one(client, recruiter_headers, talent_headers, casting_call, db_session):
    talent_a = create_talent_profile(client, talent_headers)
    other_token = register_and_verify(client, db_session, "second-talent@example.com", role="talent")
    other_headers = auth_headers(other_token)
    talent_b = create_talent_profile(client, other_headers, display_name="Second")

    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations/bulk",
        json={"talent_ids": [talent_a["id"], talent_b["id"]]},
        headers=recruiter_headers,
    )
    assert resp.status_code == 403


def test_free_recruiter_can_bulk_invite_a_single_talent(client, recruiter_headers, talent_headers, casting_call):
    talent = create_talent_profile(client, talent_headers)
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations/bulk",
        json={"talent_ids": [talent["id"]]},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert len(body["invited"]) == 1
    assert body["skipped"] == []


def test_premium_recruiter_bulk_invites_multiple_and_skips_bad_ones(
    client, recruiter_headers, talent_headers, casting_call, db_session
):
    client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers)
    talent_a = create_talent_profile(client, talent_headers)
    other_token = register_and_verify(client, db_session, "third-talent@example.com", role="talent")
    other_headers = auth_headers(other_token)
    talent_b = create_talent_profile(client, other_headers, display_name="Third")

    unknown_id = "00000000-0000-0000-0000-000000000000"
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations/bulk",
        json={"talent_ids": [talent_a["id"], talent_b["id"], unknown_id]},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert len(body["invited"]) == 2
    assert body["skipped"] == [unknown_id]

    # A repeat bulk invite for the same two talent skips them as duplicates.
    resp2 = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations/bulk",
        json={"talent_ids": [talent_a["id"], talent_b["id"]]},
        headers=recruiter_headers,
    )
    body2 = resp2.json()
    assert body2["invited"] == []
    assert sorted(body2["skipped"]) == sorted([talent_a["id"], talent_b["id"]])


def test_talent_lists_own_invitations(client, recruiter_headers, talent_headers, casting_call):
    talent = create_talent_profile(client, talent_headers)
    client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": talent["id"]},
        headers=recruiter_headers,
    )
    resp = client.get("/api/v1/talents/me/invitations", headers=talent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_recruiter_lists_invitations_for_own_call(client, recruiter_headers, talent_headers, casting_call):
    talent = create_talent_profile(client, talent_headers)
    client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": talent["id"]},
        headers=recruiter_headers,
    )
    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}/invitations", headers=recruiter_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_talent_accepts_invitation(client, recruiter_headers, talent_headers, casting_call):
    talent = create_talent_profile(client, talent_headers)
    invitation = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": talent["id"]},
        headers=recruiter_headers,
    ).json()

    resp = client.patch(f"/api/v1/invitations/{invitation['id']}", json={"status": "accepted"}, headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


def test_talent_declines_invitation(client, recruiter_headers, talent_headers, casting_call):
    talent = create_talent_profile(client, talent_headers)
    invitation = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": talent["id"]},
        headers=recruiter_headers,
    ).json()

    resp = client.patch(f"/api/v1/invitations/{invitation['id']}", json={"status": "declined"}, headers=talent_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "declined"


def test_invitation_response_rejects_invalid_status(client, recruiter_headers, talent_headers, casting_call):
    talent = create_talent_profile(client, talent_headers)
    invitation = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": talent["id"]},
        headers=recruiter_headers,
    ).json()

    resp = client.patch(f"/api/v1/invitations/{invitation['id']}", json={"status": "pending"}, headers=talent_headers)
    assert resp.status_code == 400


def test_non_invitee_talent_cannot_respond(client, recruiter_headers, talent_headers, casting_call, db_session):
    talent = create_talent_profile(client, talent_headers)
    invitation = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/invitations",
        json={"talent_id": talent["id"]},
        headers=recruiter_headers,
    ).json()

    other_token = register_and_verify(client, db_session, "notinvited@example.com", role="talent")
    other_headers = auth_headers(other_token)
    client.post("/api/v1/talents/me", json={"display_name": "Not invited", "category": "acting"}, headers=other_headers)

    resp = client.patch(f"/api/v1/invitations/{invitation['id']}", json={"status": "accepted"}, headers=other_headers)
    assert resp.status_code == 404

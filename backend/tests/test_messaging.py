from tests.conftest import register_and_verify, auth_headers


def setup_talent_and_recruiter(client, talent_headers, recruiter_headers):
    talent = client.post(
        "/api/v1/talents/me", json={"display_name": "Ishara Fernando", "category": "singing"}, headers=talent_headers
    ).json()
    recruiter = client.post(
        "/api/v1/recruiters/me", json={"company_name": "Panthera Model Management"}, headers=recruiter_headers
    ).json()
    return talent, recruiter


def test_recruiter_starts_conversation(client, talent_headers, recruiter_headers):
    talent, _ = setup_talent_and_recruiter(client, talent_headers, recruiter_headers)
    resp = client.post("/api/v1/conversations", json={"talent_id": talent["id"]}, headers=recruiter_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["talent_id"] == talent["id"]
    assert body["other_party_name"] == "Ishara Fernando"


def test_starting_conversation_twice_reuses_it(client, talent_headers, recruiter_headers):
    talent, _ = setup_talent_and_recruiter(client, talent_headers, recruiter_headers)
    first = client.post("/api/v1/conversations", json={"talent_id": talent["id"]}, headers=recruiter_headers).json()
    second = client.post("/api/v1/conversations", json={"talent_id": talent["id"]}, headers=recruiter_headers).json()
    assert first["id"] == second["id"]


def test_start_conversation_requires_recruiter_role(client, talent_headers):
    resp = client.post(
        "/api/v1/conversations",
        json={"talent_id": "00000000-0000-0000-0000-000000000000"},
        headers=talent_headers,
    )
    assert resp.status_code == 403


def test_start_conversation_unknown_talent_404(client, recruiter_headers, recruiter_profile):
    resp = client.post(
        "/api/v1/conversations",
        json={"talent_id": "00000000-0000-0000-0000-000000000000"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 404


def test_talent_sees_conversation_with_recruiter_as_other_party(client, talent_headers, recruiter_headers):
    talent, recruiter = setup_talent_and_recruiter(client, talent_headers, recruiter_headers)
    client.post("/api/v1/conversations", json={"talent_id": talent["id"]}, headers=recruiter_headers)

    resp = client.get("/api/v1/conversations", headers=talent_headers)
    assert resp.status_code == 200
    conversations = resp.json()
    assert len(conversations) == 1
    assert conversations[0]["other_party_name"] == "Panthera Model Management"


def test_send_and_receive_messages_with_unread_counts(client, talent_headers, recruiter_headers):
    talent, _ = setup_talent_and_recruiter(client, talent_headers, recruiter_headers)
    conversation = client.post("/api/v1/conversations", json={"talent_id": talent["id"]}, headers=recruiter_headers).json()

    resp = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"body": "Hi, are you available next week?"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.get("/api/v1/conversations", headers=talent_headers)
    talent_view = resp.json()[0]
    assert talent_view["unread_count"] == 1
    assert talent_view["last_message"] == "Hi, are you available next week?"

    # Fetching messages marks them read.
    resp = client.get(f"/api/v1/conversations/{conversation['id']}/messages", headers=talent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/api/v1/conversations", headers=talent_headers)
    assert resp.json()[0]["unread_count"] == 0

    # Reply back, and confirm the recruiter's side now shows unread.
    resp = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"body": "Yes, I am!"},
        headers=talent_headers,
    )
    assert resp.status_code == 201

    resp = client.get("/api/v1/conversations", headers=recruiter_headers)
    assert resp.json()[0]["unread_count"] == 1


def test_non_participant_cannot_read_messages(client, talent_headers, recruiter_headers, db_session):
    talent, _ = setup_talent_and_recruiter(client, talent_headers, recruiter_headers)
    conversation = client.post("/api/v1/conversations", json={"talent_id": talent["id"]}, headers=recruiter_headers).json()

    intruder_token = register_and_verify(client, db_session, "intruder@example.com", role="talent")
    intruder_headers = auth_headers(intruder_token)
    client.post("/api/v1/talents/me", json={"display_name": "Intruder", "category": "acting"}, headers=intruder_headers)

    resp = client.get(f"/api/v1/conversations/{conversation['id']}/messages", headers=intruder_headers)
    assert resp.status_code == 403


def test_read_messages_unknown_conversation_404(client, talent_headers):
    client.post("/api/v1/talents/me", json={"display_name": "Solo", "category": "acting"}, headers=talent_headers)
    resp = client.get(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000000/messages", headers=talent_headers
    )
    assert resp.status_code == 404

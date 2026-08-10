from tests.conftest import auth_headers, register_and_verify


def test_new_application_notifies_recruiter(client, talent_headers, talent_profile, recruiter_headers, casting_call):
    role_id = casting_call["roles"][0]["id"]
    resp = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text

    notifications = client.get("/api/v1/notifications", headers=recruiter_headers).json()
    assert any(n["type"] == "application_received" for n in notifications)

    unread = client.get("/api/v1/notifications/unread-count", headers=recruiter_headers).json()
    assert unread["count"] >= 1


def test_application_status_change_notifies_talent(client, talent_headers, talent_profile, recruiter_headers, casting_call):
    role_id = casting_call["roles"][0]["id"]
    application = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id},
        headers=talent_headers,
    ).json()

    resp = client.patch(
        f"/api/v1/applications/{application['id']}",
        json={"status": "shortlisted"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 200, resp.text

    notifications = client.get("/api/v1/notifications", headers=talent_headers).json()
    assert any(n["type"] == "application_status_changed" for n in notifications)


def test_new_message_notifies_recipient(client, recruiter_headers, recruiter_profile, talent_headers, talent_profile):
    conversation = client.post(
        "/api/v1/conversations",
        json={"talent_id": talent_profile["id"]},
        headers=recruiter_headers,
    ).json()

    resp = client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        json={"body": "Hello there"},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201, resp.text

    notifications = client.get("/api/v1/notifications", headers=talent_headers).json()
    assert any(n["type"] == "new_message" and n["body"] == "Hello there" for n in notifications)


def test_mark_notification_read_updates_unread_count(client, talent_headers, talent_profile, recruiter_headers, casting_call):
    role_id = casting_call["roles"][0]["id"]
    client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id},
        headers=talent_headers,
    )
    notifications = client.get("/api/v1/notifications", headers=recruiter_headers).json()
    notification_id = notifications[0]["id"]

    before = client.get("/api/v1/notifications/unread-count", headers=recruiter_headers).json()["count"]
    resp = client.patch(f"/api/v1/notifications/{notification_id}/read", headers=recruiter_headers)
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None
    after = client.get("/api/v1/notifications/unread-count", headers=recruiter_headers).json()["count"]
    assert after == before - 1


def test_mark_all_read_clears_unread_count(client, talent_headers, talent_profile, recruiter_headers, casting_call):
    role_id = casting_call["roles"][0]["id"]
    client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id},
        headers=talent_headers,
    )
    resp = client.patch("/api/v1/notifications/read-all", headers=recruiter_headers)
    assert resp.status_code == 204
    unread = client.get("/api/v1/notifications/unread-count", headers=recruiter_headers).json()
    assert unread["count"] == 0


def test_cannot_mark_another_users_notification_read(client, db_session, talent_headers, talent_profile, recruiter_headers, casting_call):
    role_id = casting_call["roles"][0]["id"]
    client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id},
        headers=talent_headers,
    )
    notification_id = client.get("/api/v1/notifications", headers=recruiter_headers).json()[0]["id"]

    other_token = register_and_verify(client, db_session, "other_recruiter@example.com", role="recruiter")
    other_headers = auth_headers(other_token)
    resp = client.patch(f"/api/v1/notifications/{notification_id}/read", headers=other_headers)
    assert resp.status_code == 404

import app.api.routes.casting_calls as casting_calls_routes
from tests.conftest import auth_headers, register_and_verify


class RecordingSendEmail:
    def __init__(self):
        self.calls = []

    def __call__(self, to, subject, body):
        self.calls.append({"to": to, "subject": subject, "body": body})


def test_talent_follows_and_lists_recruiter(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    resp = client.post(f"/api/v1/recruiters/{recruiter_profile['id']}/follow", headers=talent_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["recruiter_id"] == recruiter_profile["id"]
    assert body["recruiter_company_name"] == recruiter_profile["company_name"]

    resp = client.get("/api/v1/talents/me/following", headers=talent_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_talent_unfollows_recruiter(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    client.post(f"/api/v1/recruiters/{recruiter_profile['id']}/follow", headers=talent_headers)
    resp = client.delete(f"/api/v1/recruiters/{recruiter_profile['id']}/follow", headers=talent_headers)
    assert resp.status_code == 204

    resp = client.get("/api/v1/talents/me/following", headers=talent_headers)
    assert resp.json() == []


def test_duplicate_follow_rejected(client, talent_headers, talent_profile, recruiter_headers, recruiter_profile):
    client.post(f"/api/v1/recruiters/{recruiter_profile['id']}/follow", headers=talent_headers)
    resp = client.post(f"/api/v1/recruiters/{recruiter_profile['id']}/follow", headers=talent_headers)
    assert resp.status_code == 400


def test_follow_unknown_recruiter_404(client, talent_headers, talent_profile):
    resp = client.post(
        "/api/v1/recruiters/00000000-0000-0000-0000-000000000000/follow", headers=talent_headers
    )
    assert resp.status_code == 404


def test_recruiter_cannot_follow(client, recruiter_headers, recruiter_profile):
    resp = client.post(f"/api/v1/recruiters/{recruiter_profile['id']}/follow", headers=recruiter_headers)
    assert resp.status_code == 403


def test_follower_is_emailed_when_recruiter_posts_new_casting_call(
    client, db_session, monkeypatch, talent_headers, talent_profile, recruiter_headers, recruiter_profile
):
    recorder = RecordingSendEmail()
    monkeypatch.setattr(casting_calls_routes, "send_email", recorder)

    client.post(f"/api/v1/recruiters/{recruiter_profile['id']}/follow", headers=talent_headers)

    other_token = register_and_verify(client, db_session, "notfollowing@example.com", role="talent")
    client.post(
        "/api/v1/talents/me",
        json={"display_name": "Not Following", "category": "dancing"},
        headers=auth_headers(other_token),
    )

    resp = client.post(
        "/api/v1/casting-calls",
        json={"title": "Follower gig", "description": "x", "category": "singing", "roles": [{"title": "x"}]},
        headers=recruiter_headers,
    )
    assert resp.status_code == 201

    recipients = [c["to"] for c in recorder.calls]
    assert "talent_fixture@example.com" in recipients
    assert "notfollowing@example.com" not in recipients

import app.api.routes.casting_calls as casting_calls_routes
from tests.conftest import register_and_verify, auth_headers


class RecordingSendEmail:
    def __init__(self):
        self.calls = []

    def __call__(self, to, subject, body):
        self.calls.append({"to": to, "subject": subject, "body": body})


def create_talent(client, headers, **overrides):
    payload = {"display_name": "Talent", "category": "modeling"}
    payload.update(overrides)
    return client.post("/api/v1/talents/me", json=payload, headers=headers).json()


def post_casting_call(client, recruiter_headers, **overrides):
    payload = {
        "title": "New modeling gig",
        "description": "x",
        "category": "modeling",
        "roles": [{"title": "x"}],
    }
    payload.update(overrides)
    return client.post("/api/v1/casting-calls", json=payload, headers=recruiter_headers)


def test_matching_category_talent_is_emailed(client, db_session, monkeypatch, recruiter_headers, recruiter_profile):
    recorder = RecordingSendEmail()
    monkeypatch.setattr(casting_calls_routes, "send_email", recorder)

    talent_token = register_and_verify(client, db_session, "modeltalent@example.com", role="talent")
    create_talent(client, auth_headers(talent_token), category="modeling")

    resp = post_casting_call(client, recruiter_headers, category="modeling")
    assert resp.status_code == 201

    recipients = [c["to"] for c in recorder.calls]
    assert "modeltalent@example.com" in recipients


def test_non_matching_category_talent_is_not_emailed(client, db_session, monkeypatch, recruiter_headers, recruiter_profile):
    recorder = RecordingSendEmail()
    monkeypatch.setattr(casting_calls_routes, "send_email", recorder)

    actor_token = register_and_verify(client, db_session, "actortalent@example.com", role="talent")
    create_talent(client, auth_headers(actor_token), category="acting")

    resp = post_casting_call(client, recruiter_headers, category="modeling")
    assert resp.status_code == 201

    recipients = [c["to"] for c in recorder.calls]
    assert "actortalent@example.com" not in recipients


def test_opted_out_talent_is_not_emailed(client, db_session, monkeypatch, recruiter_headers, recruiter_profile):
    recorder = RecordingSendEmail()
    monkeypatch.setattr(casting_calls_routes, "send_email", recorder)

    talent_token = register_and_verify(client, db_session, "optedout@example.com", role="talent")
    talent_headers = auth_headers(talent_token)
    create_talent(client, talent_headers, category="modeling")
    client.patch("/api/v1/talents/me", json={"job_alert_emails": False}, headers=talent_headers)

    resp = post_casting_call(client, recruiter_headers, category="modeling")
    assert resp.status_code == 201

    recipients = [c["to"] for c in recorder.calls]
    assert "optedout@example.com" not in recipients


def test_role_level_category_also_triggers_a_match(client, db_session, monkeypatch, recruiter_headers, recruiter_profile):
    recorder = RecordingSendEmail()
    monkeypatch.setattr(casting_calls_routes, "send_email", recorder)

    actor_token = register_and_verify(client, db_session, "roleactor@example.com", role="talent")
    create_talent(client, auth_headers(actor_token), category="acting")
    assert client.post("/api/v1/recruiters/me/upgrade", headers=recruiter_headers).status_code == 200

    # The overall call is "modeling", but one of its roles is specifically for actors —
    # an actor should still be matched via that role's category.
    resp = post_casting_call(
        client,
        recruiter_headers,
        category="modeling",
        roles=[{"title": "Models"}, {"title": "Actors", "category": "acting"}],
    )
    assert resp.status_code == 201

    recipients = [c["to"] for c in recorder.calls]
    assert "roleactor@example.com" in recipients


def test_secondary_category_still_triggers_a_match(client, db_session, monkeypatch, recruiter_headers, recruiter_profile):
    # A talent whose PRIMARY category is acting but who also does modeling as a secondary
    # category must still be matched by a modeling-only casting call — this is the exact
    # array-overlap behavior the multi-category migration must preserve.
    recorder = RecordingSendEmail()
    monkeypatch.setattr(casting_calls_routes, "send_email", recorder)

    talent_token = register_and_verify(client, db_session, "multitalent@example.com", role="talent")
    create_talent(client, auth_headers(talent_token), categories=["acting", "modeling"])

    resp = post_casting_call(client, recruiter_headers, category="modeling")
    assert resp.status_code == 201

    recipients = [c["to"] for c in recorder.calls]
    assert "multitalent@example.com" in recipients


def test_multiple_matching_talents_all_emailed(client, db_session, monkeypatch, recruiter_headers, recruiter_profile):
    recorder = RecordingSendEmail()
    monkeypatch.setattr(casting_calls_routes, "send_email", recorder)

    for email in ("model1@example.com", "model2@example.com"):
        token = register_and_verify(client, db_session, email, role="talent")
        create_talent(client, auth_headers(token), category="modeling")

    resp = post_casting_call(client, recruiter_headers, category="modeling")
    assert resp.status_code == 201

    recipients = {c["to"] for c in recorder.calls}
    assert {"model1@example.com", "model2@example.com"}.issubset(recipients)

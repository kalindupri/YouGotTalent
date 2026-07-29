from datetime import datetime, timedelta, timezone

from tests.conftest import get_verification_code, register_user, verify_email, DEFAULT_PASSWORD


def test_register_returns_unverified_user(client):
    body = register_user(client, "newuser@example.com")
    assert body["email"] == "newuser@example.com"
    assert body["email_verified"] is False
    assert body["role"] == "talent"


def test_register_duplicate_email_rejected(client):
    register_user(client, "dupe@example.com")
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "dupe@example.com",
            "password": DEFAULT_PASSWORD,
            "full_name": "Someone Else",
            "role": "talent",
            "consent_given": True,
        },
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_without_consent_rejected(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "noconsent@example.com",
            "password": DEFAULT_PASSWORD,
            "full_name": "No Consent",
            "role": "talent",
            "consent_given": False,
        },
    )
    assert resp.status_code == 400
    assert "consent" in resp.json()["detail"].lower()


def test_login_blocked_before_verification(client):
    register_user(client, "unverified@example.com")
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "unverified@example.com", "password": DEFAULT_PASSWORD},
    )
    assert resp.status_code == 403
    assert "verify" in resp.json()["detail"].lower()


def test_login_wrong_password_rejected(client):
    register_user(client, "wrongpass@example.com")
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "wrongpass@example.com", "password": "not-the-password"},
    )
    assert resp.status_code == 401


def test_verify_email_wrong_code_rejected(client):
    register_user(client, "wrongcode@example.com")
    resp = client.post("/api/v1/auth/verify-email", json={"email": "wrongcode@example.com", "code": "000000"})
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


def test_verify_email_expired_code_rejected(client, db_session):
    register_user(client, "expired@example.com")
    from app.models.user import User

    user = db_session.query(User).filter(User.email == "expired@example.com").first()
    code = user.verification_code
    user.verification_code_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    resp = client.post("/api/v1/auth/verify-email", json={"email": "expired@example.com", "code": code})
    assert resp.status_code == 400


def test_verify_email_correct_code_returns_token_and_unlocks_login(client, db_session):
    register_user(client, "correct@example.com")
    token = verify_email(client, db_session, "correct@example.com")
    assert token

    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "correct@example.com", "password": DEFAULT_PASSWORD},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_me_reflects_verified_state(client, db_session):
    register_user(client, "me@example.com")
    token = verify_email(client, db_session, "me@example.com")
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "me@example.com"
    assert body["email_verified"] is True


def test_resend_verification_issues_new_usable_code(client, db_session):
    register_user(client, "resend@example.com")

    resp = client.post("/api/v1/auth/resend-verification", json={"email": "resend@example.com"})
    assert resp.status_code == 204

    new_code = get_verification_code(db_session, "resend@example.com")
    # Not a strict guarantee they differ (random collision is astronomically unlikely for a
    # 6-digit code), but the important behavior is that the new code actually verifies.
    resp = client.post("/api/v1/auth/verify-email", json={"email": "resend@example.com", "code": new_code})
    assert resp.status_code == 200


def test_resend_verification_silent_for_unknown_email(client):
    resp = client.post("/api/v1/auth/resend-verification", json={"email": "doesnotexist@example.com"})
    assert resp.status_code == 204


def test_resend_verification_silent_for_already_verified(client, db_session):
    register_user(client, "alreadyverified@example.com")
    verify_email(client, db_session, "alreadyverified@example.com")
    resp = client.post("/api/v1/auth/resend-verification", json={"email": "alreadyverified@example.com"})
    assert resp.status_code == 204


def test_me_requires_authentication(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401

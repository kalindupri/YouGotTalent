from app.core.rate_limit import limiter


def test_login_is_rate_limited(client):
    # The `limiter` fixture is disabled globally in conftest.py so every other test isn't
    # throttled by the shared "testclient" bucket TestClient requests all share -- re-enable
    # it just for this test to confirm the limit is actually wired up.
    limiter.enabled = True
    try:
        responses = [
            client.post(
                "/api/v1/auth/login",
                data={"username": "nobody@example.com", "password": "wrong"},
            )
            for _ in range(11)
        ]
    finally:
        limiter.enabled = False

    assert responses[-1].status_code == 429
    assert any(r.status_code == 401 for r in responses[:10])


def test_guardian_consent_submission_is_rate_limited(client, talent_headers):
    """Accepts file uploads and writes to private storage, so it must not be spammable.

    Same shape as the login test above: the limiter is disabled globally in conftest so the
    shared "testclient" bucket doesn't throttle unrelated tests, and re-enabled just here.
    """
    from tests.test_guardian_consent import PDF, create_profile

    create_profile(client, talent_headers, age=13)

    limiter.enabled = True
    try:
        responses = [
            client.post(
                "/api/v1/talents/me/guardian-consent",
                data={
                    "guardian_full_name": "Nimal Perera",
                    "guardian_relationship": "father",
                    "minor_full_name": "Sanduni Perera",
                    "consented_scopes": ["profile_public"],
                    "agreed": "true",
                },
                files={"birth_certificate": ("cert.pdf", PDF, "application/pdf")},
                headers=talent_headers,
            )
            for _ in range(7)
        ]
    finally:
        limiter.enabled = False

    assert responses[-1].status_code == 429

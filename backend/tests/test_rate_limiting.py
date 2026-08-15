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

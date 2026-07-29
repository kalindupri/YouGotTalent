def test_health_endpoint_reachable(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_creates_unverified_user(client, db_session):
    from tests.conftest import register_user, get_verification_code

    register_user(client, "smoke@example.com")
    code = get_verification_code(db_session, "smoke@example.com")
    assert len(code) == 6

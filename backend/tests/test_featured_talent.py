from tests.conftest import auth_headers, register_and_verify
from tests.test_talent_profiles import create_profile


def test_featured_talent_excludes_free_and_unverified(client, talent_headers, db_session):
    create_profile(client, talent_headers, display_name="Free Talent")
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)

    resp = client.get("/api/v1/talents/featured")
    assert resp.status_code == 200
    # Premium but not verified yet — verification is manual/admin-only, so still excluded.
    assert resp.json() == []


def test_featured_talent_includes_premium_and_verified(client, talent_headers, db_session):
    from app.models.talent_profile import TalentProfile

    profile = create_profile(client, talent_headers, display_name="Featured Talent")
    client.post("/api/v1/talents/me/upgrade", headers=talent_headers)

    row = db_session.query(TalentProfile).filter(TalentProfile.id == profile["id"]).first()
    row.is_verified = True
    db_session.commit()

    resp = client.get("/api/v1/talents/featured")
    assert resp.status_code == 200
    ids = {t["id"] for t in resp.json()}
    assert profile["id"] in ids

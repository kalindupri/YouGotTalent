from tests.conftest import ADULT_DOB, auth_headers, register_and_verify


def add_reel(client, headers, *, url="https://www.tiktok.com/@user/video/123", caption=None):
    payload = {"url": url}
    if caption is not None:
        payload["caption"] = caption
    return client.post("/api/v1/talents/me/reels", json=payload, headers=headers)


def test_free_talent_cannot_add_reel(client, talent_headers, talent_profile):
    resp = add_reel(client, talent_headers)
    assert resp.status_code == 403
    assert "Premium" in resp.json()["detail"]


def test_premium_talent_can_add_reel_and_it_appears_on_public_profile(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    resp = add_reel(client, talent_headers, url="https://www.instagram.com/reel/abc123/", caption="Behind the scenes")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["platform"] == "instagram"
    assert body["url"] == "https://www.instagram.com/reel/abc123/"
    assert body["caption"] == "Behind the scenes"

    profile_resp = client.get(f"/api/v1/talents/{talent_profile['id']}")
    assert profile_resp.status_code == 200
    reels = profile_resp.json()["reels"]
    assert len(reels) == 1
    assert reels[0]["platform"] == "instagram"


def test_reel_platform_detection_tiktok_and_facebook(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    tiktok_resp = add_reel(client, talent_headers, url="https://www.tiktok.com/@user/video/123")
    assert tiktok_resp.status_code == 201, tiktok_resp.text
    assert tiktok_resp.json()["platform"] == "tiktok"

    fb_resp = add_reel(client, talent_headers, url="https://www.facebook.com/reel/456")
    assert fb_resp.status_code == 201, fb_resp.text
    assert fb_resp.json()["platform"] == "facebook"


def test_reel_rejects_unrecognized_domain(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    resp = add_reel(client, talent_headers, url="https://www.google.com/search?q=hi")
    assert resp.status_code == 400
    assert "TikTok" in resp.json()["detail"]


def test_reel_limit_enforced(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    for i in range(10):
        resp = add_reel(client, talent_headers, url=f"https://www.tiktok.com/@user/video/{i}")
        assert resp.status_code == 201, resp.text

    resp = add_reel(client, talent_headers, url="https://www.tiktok.com/@user/video/overflow")
    assert resp.status_code == 403
    assert "limit" in resp.json()["detail"].lower()


def test_talent_deletes_own_reel(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    reel = add_reel(client, talent_headers).json()

    resp = client.delete(f"/api/v1/talents/me/reels/{reel['id']}", headers=talent_headers)
    assert resp.status_code == 204

    profile_resp = client.get(f"/api/v1/talents/{talent_profile['id']}")
    assert profile_resp.json()["reels"] == []


def test_talent_cannot_delete_another_talents_reel(client, db_session, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    reel = add_reel(client, talent_headers).json()

    other_token = register_and_verify(client, db_session, "other_talent_reels@example.com", full_name="Other Talent")
    other_headers = auth_headers(other_token)
    resp = client.post(
        "/api/v1/talents/me",
        json={"date_of_birth": ADULT_DOB, "display_name": "Other Talent", "category": "acting", "city": "Kandy"},
        headers=other_headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.delete(f"/api/v1/talents/me/reels/{reel['id']}", headers=other_headers)
    assert resp.status_code == 404


def test_downgraded_talent_keeps_existing_reel_but_cannot_add(client, talent_headers, talent_profile, db_session):
    from app.models.talent_profile import TalentProfile

    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    add_reel(client, talent_headers)

    row = db_session.query(TalentProfile).filter(TalentProfile.id == talent_profile["id"]).first()
    row.tier = "free"
    db_session.commit()

    profile_resp = client.get(f"/api/v1/talents/{talent_profile['id']}")
    assert len(profile_resp.json()["reels"]) == 1

    resp = add_reel(client, talent_headers, url="https://www.tiktok.com/@user/video/999")
    assert resp.status_code == 403

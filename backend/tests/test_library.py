from tests.conftest import auth_headers, register_and_verify


def upload_library_photo(client, headers, photo_bytes, *, title="My work"):
    return client.post(
        "/api/v1/talents/me/library/upload",
        data={"media_type": "photo", "title": title},
        files={"file": ("sample.jpg", photo_bytes, "image/jpeg")},
        headers=headers,
    )


def upload_library_audio(client, headers, audio_bytes, *, title="My track"):
    return client.post(
        "/api/v1/talents/me/library/upload",
        data={"media_type": "audio", "title": title},
        files={"file": ("sample.mp3", audio_bytes, "audio/mpeg")},
        headers=headers,
    )


def create_url_item(client, headers, *, title="External track", url="https://soundcloud.com/example/track"):
    return client.post(
        "/api/v1/talents/me/library",
        json={"title": title, "media_type": "audio", "url": url, "description": "A track"},
        headers=headers,
    )


def test_free_talent_cannot_create_url_library_item(client, talent_headers, talent_profile):
    resp = create_url_item(client, talent_headers)
    assert resp.status_code == 403
    assert "Premium" in resp.json()["detail"]


def test_free_talent_cannot_upload_library_item(client, talent_headers, talent_profile, sample_photo_bytes):
    resp = upload_library_photo(client, talent_headers, sample_photo_bytes)
    assert resp.status_code == 403


def test_premium_talent_can_create_url_library_item(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    resp = create_url_item(client, talent_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "External track"
    assert body["media_type"] == "audio"
    assert body["url"] == "https://soundcloud.com/example/track"


def test_premium_talent_can_upload_photo_and_audio(client, talent_headers, talent_profile, sample_photo_bytes, sample_audio_bytes):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    photo_resp = upload_library_photo(client, talent_headers, sample_photo_bytes, title="Headshot series")
    assert photo_resp.status_code == 201, photo_resp.text
    assert photo_resp.json()["media_type"] == "photo"

    audio_resp = upload_library_audio(client, talent_headers, sample_audio_bytes, title="Demo reel")
    assert audio_resp.status_code == 201, audio_resp.text
    assert audio_resp.json()["media_type"] == "audio"


def test_library_upload_rejects_document_type(client, talent_headers, talent_profile, sample_photo_bytes):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    resp = client.post(
        "/api/v1/talents/me/library/upload",
        data={"media_type": "document", "title": "x"},
        files={"file": ("sample.jpg", sample_photo_bytes, "image/jpeg")},
        headers=talent_headers,
    )
    assert resp.status_code == 400


def test_talent_lists_own_library_items_newest_first(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    create_url_item(client, talent_headers, title="First", url="https://example.com/1")
    create_url_item(client, talent_headers, title="Second", url="https://example.com/2")

    resp = client.get("/api/v1/talents/me/library", headers=talent_headers)
    assert resp.status_code == 200
    titles = [item["title"] for item in resp.json()]
    assert titles == ["Second", "First"]


def test_talent_deletes_own_library_item(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    item = create_url_item(client, talent_headers).json()

    resp = client.delete(f"/api/v1/talents/me/library/{item['id']}", headers=talent_headers)
    assert resp.status_code == 204

    resp = client.get("/api/v1/talents/me/library", headers=talent_headers)
    assert resp.json() == []


def test_talent_cannot_delete_another_talents_library_item(client, db_session, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    item = create_url_item(client, talent_headers).json()

    other_token = register_and_verify(client, db_session, "other_talent_library@example.com", full_name="Other Talent")
    other_headers = auth_headers(other_token)
    resp = client.post(
        "/api/v1/talents/me",
        json={"display_name": "Other Talent", "category": "acting", "city": "Kandy"},
        headers=other_headers,
    )
    assert resp.status_code == 201, resp.text

    resp = client.delete(f"/api/v1/talents/me/library/{item['id']}", headers=other_headers)
    assert resp.status_code == 404


def test_downgraded_talent_can_still_delete_but_not_add(client, db_session, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    item = create_url_item(client, talent_headers).json()

    from datetime import datetime, timedelta, timezone

    from app.models.subscription import Subscription

    sub = db_session.query(Subscription).filter(Subscription.talent_profile_id == talent_profile["id"]).first()
    sub.trial_end = datetime.now(timezone.utc) - timedelta(days=1)
    db_session.commit()

    # Lazily reconciled back to free on the next profile fetch.
    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    assert resp.json()["tier"] == "free"

    resp = create_url_item(client, talent_headers, title="Should fail", url="https://example.com/x")
    assert resp.status_code == 403

    resp = client.delete(f"/api/v1/talents/me/library/{item['id']}", headers=talent_headers)
    assert resp.status_code == 204


def test_public_can_view_talent_library(client, talent_headers, talent_profile):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200
    create_url_item(client, talent_headers, title="Public track", url="https://example.com/public")

    resp = client.get(f"/api/v1/talents/{talent_profile['id']}/library")
    assert resp.status_code == 200
    titles = [item["title"] for item in resp.json()]
    assert "Public track" in titles


def test_library_for_unknown_talent_returns_404(client):
    resp = client.get("/api/v1/talents/00000000-0000-0000-0000-000000000000/library")
    assert resp.status_code == 404

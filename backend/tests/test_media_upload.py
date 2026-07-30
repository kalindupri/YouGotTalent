def upload_video(client, headers, video_bytes, *, title=None):
    data = {"media_type": "video"}
    if title:
        data["title"] = title
    return client.post(
        "/api/v1/talents/me/media/upload",
        data=data,
        files={"file": ("sample.mp4", video_bytes, "video/mp4")},
        headers=headers,
    )


def upload_audio(client, headers, audio_bytes, *, title=None):
    data = {"media_type": "audio"}
    if title:
        data["title"] = title
    return client.post(
        "/api/v1/talents/me/media/upload",
        data=data,
        files={"file": ("sample.mp3", audio_bytes, "audio/mpeg")},
        headers=headers,
    )


def test_upload_video_success(client, talent_headers, talent_profile, sample_video_bytes):
    resp = upload_video(client, talent_headers, sample_video_bytes, title="My audition")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["media_type"] == "video"
    assert body["title"] == "My audition"
    assert body["url"]


def test_upload_audio_success(client, talent_headers, talent_profile, sample_audio_bytes):
    resp = upload_audio(client, talent_headers, sample_audio_bytes)
    assert resp.status_code == 201, resp.text
    assert resp.json()["media_type"] == "audio"


def test_upload_video_free_tier_limit_is_one(client, talent_headers, talent_profile, sample_video_bytes):
    first = upload_video(client, talent_headers, sample_video_bytes)
    assert first.status_code == 201

    second = upload_video(client, talent_headers, sample_video_bytes)
    assert second.status_code == 403
    assert "1 audition video" in second.json()["detail"]


def test_upload_video_premium_tier_limit_is_five(client, talent_headers, talent_profile, sample_video_bytes):
    upgrade = client.post("/api/v1/talents/me/upgrade", headers=talent_headers)
    assert upgrade.status_code == 200
    assert upgrade.json()["tier"] == "premium"

    for _ in range(5):
        resp = upload_video(client, talent_headers, sample_video_bytes)
        assert resp.status_code == 201, resp.text

    sixth = upload_video(client, talent_headers, sample_video_bytes)
    assert sixth.status_code == 403
    assert "5 audition video" in sixth.json()["detail"]


def test_upload_audio_still_respects_general_free_tier_limit(client, talent_headers, talent_profile, sample_audio_bytes):
    for _ in range(3):
        resp = upload_audio(client, talent_headers, sample_audio_bytes)
        assert resp.status_code == 201, resp.text

    fourth = upload_audio(client, talent_headers, sample_audio_bytes)
    assert fourth.status_code == 403
    assert "premium" in fourth.json()["detail"].lower()


def test_upload_rejects_unsupported_media_type(client, talent_headers, talent_profile, sample_video_bytes):
    resp = client.post(
        "/api/v1/talents/me/media/upload",
        data={"media_type": "photo"},
        files={"file": ("sample.jpg", sample_video_bytes, "image/jpeg")},
        headers=talent_headers,
    )
    assert resp.status_code == 400


def test_upload_rejects_corrupt_video_file(client, talent_headers, talent_profile):
    resp = upload_video(client, talent_headers, b"not a real video file")
    assert resp.status_code == 400

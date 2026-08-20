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


def upload_cover_photo(client, headers, photo_bytes):
    return client.post(
        "/api/v1/talents/me/cover-photo",
        files={"file": ("headshot.jpg", photo_bytes, "image/jpeg")},
        headers=headers,
    )


def test_upload_cover_photo_success(client, talent_headers, talent_profile, sample_photo_bytes):
    resp = upload_cover_photo(client, talent_headers, sample_photo_bytes)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["media_type"] == "photo"
    assert body["is_cover"] is True
    assert body["title"] == "Profile photo"


def test_first_cover_photo_respects_free_tier_quota(client, talent_headers, talent_profile, sample_photo_bytes):
    for _ in range(3):
        resp = client.post(
            "/api/v1/talents/me/media",
            json={"url": "https://example.com/photo.jpg", "media_type": "photo"},
            headers=talent_headers,
        )
        assert resp.status_code == 201, resp.text

    resp = upload_cover_photo(client, talent_headers, sample_photo_bytes)
    assert resp.status_code == 403


def test_replacing_cover_photo_does_not_cost_a_quota_slot(client, talent_headers, talent_profile, sample_photo_bytes):
    first = upload_cover_photo(client, talent_headers, sample_photo_bytes)
    assert first.status_code == 201, first.text

    # The cover photo counts toward the general 3-item quota like any other media, so only
    # 2 more portfolio photos fit alongside it.
    for _ in range(2):
        resp = client.post(
            "/api/v1/talents/me/media",
            json={"url": "https://example.com/photo.jpg", "media_type": "photo"},
            headers=talent_headers,
        )
        assert resp.status_code == 201, resp.text

    # The 3-item quota is now fully used, but replacing the existing cover photo deletes
    # the old one first, so it should never 403.
    replaced = upload_cover_photo(client, talent_headers, sample_photo_bytes)
    assert replaced.status_code == 201, replaced.text

    resp = client.get("/api/v1/talents/me", headers=talent_headers)
    cover_photos = [m for m in resp.json()["media"] if m["is_cover"]]
    assert len(cover_photos) == 1


def test_upload_cover_photo_rejects_corrupt_file(client, talent_headers, talent_profile):
    resp = upload_cover_photo(client, talent_headers, b"not a real image file")
    assert resp.status_code == 400


def upload_intro_video(client, headers, video_bytes):
    return client.post(
        "/api/v1/talents/me/intro-video",
        files={"file": ("intro.mp4", video_bytes, "video/mp4")},
        headers=headers,
    )


def test_upload_intro_video_success(client, talent_headers, talent_profile, sample_video_bytes):
    resp = upload_intro_video(client, talent_headers, sample_video_bytes)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["intro_video_url"]


def test_replacing_intro_video_does_not_error(client, talent_headers, talent_profile, sample_video_bytes):
    first = upload_intro_video(client, talent_headers, sample_video_bytes)
    assert first.status_code == 201, first.text
    first_url = first.json()["intro_video_url"]

    second = upload_intro_video(client, talent_headers, sample_video_bytes)
    assert second.status_code == 201, second.text
    assert second.json()["intro_video_url"] != first_url


def test_upload_intro_video_rejects_corrupt_file(client, talent_headers, talent_profile):
    resp = upload_intro_video(client, talent_headers, b"not a real video file")
    assert resp.status_code == 400


def test_upload_video_rejects_over_30_seconds(client, talent_headers, talent_profile, long_sample_video_bytes):
    resp = upload_video(client, talent_headers, long_sample_video_bytes)
    assert resp.status_code == 400
    assert "30 seconds" in resp.json()["detail"]


def test_upload_intro_video_rejects_over_30_seconds(client, talent_headers, talent_profile, long_sample_video_bytes):
    resp = upload_intro_video(client, talent_headers, long_sample_video_bytes)
    assert resp.status_code == 400
    assert "30 seconds" in resp.json()["detail"]


# --- Transcode fast path -------------------------------------------------------------------
#
# A full re-encode of a 30s 1080p clip costs ~35s on the 0.5 vCPU the app runs with in Azure,
# spent inside the upload request. compress_video skips it when the source is already
# H.264/AAC at our target size. These pin both branches of that decision.

def _encode(tmp_path, name, *, size, bitrate, vcodec="libx264", acodec="aac"):
    import subprocess

    path = tmp_path / name
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"testsrc=duration=2:size={size}:rate=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-shortest", "-pix_fmt", "yuv420p",
            # Forced CBR: testsrc's flat colour bars compress so well that a plain -b:v target
            # is ignored, and the "too fat to serve as-is" case would silently not be that.
            "-c:v", vcodec, "-b:v", bitrate, "-minrate", bitrate, "-maxrate", bitrate,
            "-bufsize", bitrate, "-c:a", acodec,
            str(path),
        ],
        check=True,
        capture_output=True,
    )
    return str(path)


def test_web_ready_source_is_remuxed_not_re_encoded(tmp_path):
    from app.core.media_processing import _remux_if_already_web_ready

    source = _encode(tmp_path, "ready.mp4", size="1280x720", bitrate="1000k")
    assert _remux_if_already_web_ready(source, str(tmp_path / "out.mp4")) is True
    assert (tmp_path / "out.mp4").stat().st_size > 0


def test_oversized_source_still_gets_transcoded(tmp_path):
    from app.core.media_processing import _remux_if_already_web_ready

    # Wider than the 1280px target, so serving it as-is would defeat the compression entirely.
    source = _encode(tmp_path, "big.mp4", size="1920x1080", bitrate="1000k")
    assert _remux_if_already_web_ready(source, str(tmp_path / "out.mp4")) is False


def test_high_bitrate_source_still_gets_transcoded(tmp_path, monkeypatch):
    # Stubbed probe rather than a real fat file: x264 won't inflate a synthetic source to a high
    # bitrate no matter what rate control asks for, and the rule under test is the decision, not
    # ffmpeg's rate control.
    from app.core import media_processing

    monkeypatch.setattr(
        media_processing,
        "_stream_info",
        lambda path: {
            "video": {"codec_name": "h264", "width": 1280, "bit_rate": "6000000"},
            "audio": {"codec_name": "aac"},
            "format": {},
        },
    )
    assert media_processing._remux_if_already_web_ready("in.mp4", str(tmp_path / "out.mp4")) is False


def test_non_h264_source_still_gets_transcoded(tmp_path, monkeypatch):
    # HEVC is what modern iPhones record by default and most browsers won't play it.
    from app.core import media_processing

    monkeypatch.setattr(
        media_processing,
        "_stream_info",
        lambda path: {
            "video": {"codec_name": "hevc", "width": 1280, "bit_rate": "800000"},
            "audio": {"codec_name": "aac"},
            "format": {},
        },
    )
    assert media_processing._remux_if_already_web_ready("in.mp4", str(tmp_path / "out.mp4")) is False


def test_unprobeable_source_falls_back_to_transcoding(tmp_path, monkeypatch):
    from app.core import media_processing

    monkeypatch.setattr(media_processing, "_stream_info", lambda path: {})
    assert media_processing._remux_if_already_web_ready("in.mp4", str(tmp_path / "out.mp4")) is False


def test_compress_video_produces_output_either_way(tmp_path):
    from app.core.media_processing import compress_video

    for name, size in (("ready2.mp4", "1280x720"), ("big2.mp4", "1920x1080")):
        source = _encode(tmp_path, name, size=size, bitrate="1000k")
        out = tmp_path / f"out-{name}"
        compress_video(source, str(out))
        assert out.stat().st_size > 0


# --- Per-tier upload limits ----------------------------------------------------------------

def test_free_talent_video_is_capped_at_thirty_seconds(client, talent_headers, talent_profile, long_sample_video_bytes):
    resp = client.post(
        "/api/v1/talents/me/media/upload",
        data={"media_type": "video", "title": "Long take"},
        files={"file": ("sample.mp4", long_sample_video_bytes, "video/mp4")},
        headers=talent_headers,
    )
    assert resp.status_code == 400
    assert "30 seconds" in resp.json()["detail"]
    # Free users are told the upgrade actually buys them something.
    assert "Premium" in resp.json()["detail"]


def test_premium_talent_video_is_capped_at_two_minutes(client, talent_headers, talent_profile, long_sample_video_bytes):
    assert client.post("/api/v1/talents/me/upgrade", headers=talent_headers).status_code == 200

    # 35s: over the free cap, well inside Premium's.
    resp = client.post(
        "/api/v1/talents/me/media/upload",
        data={"media_type": "video", "title": "Long take"},
        files={"file": ("sample.mp4", long_sample_video_bytes, "video/mp4")},
        headers=talent_headers,
    )
    assert resp.status_code == 201, resp.text


def test_tier_limit_helpers_agree_with_settings():
    from app.core.config import settings
    from app.core.upload_limits import max_upload_size_for, max_video_duration_for

    assert max_video_duration_for("free") == settings.MAX_VIDEO_DURATION_SECONDS == 30
    assert max_video_duration_for("premium") == settings.PREMIUM_MAX_VIDEO_DURATION_SECONDS == 120
    assert max_upload_size_for("free") == settings.MAX_UPLOAD_SIZE_BYTES == 75 * 1024 * 1024
    assert max_upload_size_for("premium") == settings.PREMIUM_MAX_UPLOAD_SIZE_BYTES == 150 * 1024 * 1024
    # An unknown/None tier must fall to the free limits, never the premium ones.
    assert max_video_duration_for(None) == settings.MAX_VIDEO_DURATION_SECONDS
    assert max_upload_size_for("nonsense") == settings.MAX_UPLOAD_SIZE_BYTES

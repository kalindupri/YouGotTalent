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


# --- Diagnosing processing failures ---------------------------------------------------------
#
# Every upload route catches MediaProcessingError to build a user-facing message. Before these,
# ffmpeg's stderr was discarded at that point, so a failing upload left nothing in the logs to
# explain it -- the 400 was all anyone, user or operator, ever saw.

def test_ffmpeg_stderr_is_logged_when_processing_fails(tmp_path, caplog):
    import logging

    from app.core.media_processing import MediaProcessingError, compress_video

    bogus = tmp_path / "notavideo.mov"
    bogus.write_bytes(b"\x00" * 4096)

    with caplog.at_level(logging.WARNING, logger="app.core.media_processing"):
        try:
            compress_video(str(bogus), str(tmp_path / "out.mp4"))
        except MediaProcessingError:
            pass

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "ffmpeg exited" in logged
    # The actual reason has to survive, not just the fact that something failed.
    assert "moov atom not found" in logged or "Invalid data" in logged


def test_processing_timeout_is_not_reported_as_an_invalid_file():
    from app.core.media_processing import MediaProcessingError, MediaProcessingTimeout
    from app.core.upload_limits import media_processing_http_error

    timeout = media_processing_http_error(MediaProcessingTimeout("x"), noun="file")
    invalid = media_processing_http_error(MediaProcessingError("x"), noun="file")

    # Running out of our own CPU budget must not tell someone their good video is broken.
    assert "took too long" in timeout.detail
    assert "valid" not in timeout.detail
    assert "valid" in invalid.detail
    assert timeout.status_code == invalid.status_code == 400


def test_processing_timeout_scales_with_the_longest_clip_we_accept():
    from app.core.config import settings
    from app.core.media_processing import COMPRESS_TIMEOUT_SECONDS

    # Derived, not hardcoded: raising a duration cap must never leave uploads timing out. The
    # API runs on 0.5 vCPU, where a detailed 1080p source transcodes at roughly real time.
    assert COMPRESS_TIMEOUT_SECONDS >= settings.PREMIUM_MAX_VIDEO_DURATION_SECONDS * 4


def test_ffmpeg_stderr_is_never_echoed_to_the_client():
    from app.core.media_processing import MediaProcessingError
    from app.core.upload_limits import media_processing_http_error

    exc = MediaProcessingError("/app/private_uploads/secret.mov: Invalid data at 0x7fff")
    detail = media_processing_http_error(exc, noun="file").detail
    assert "private_uploads" not in detail and "0x7fff" not in detail


# --- Memory safety --------------------------------------------------------------------------
#
# A .mov upload died on UAT with "ffmpeg exited -9" -- SIGKILL, i.e. the OOM killer, with x264
# reporting threads=6. ffmpeg sizes its pool from the *node's* cores (12) rather than the 0.5
# vCPU the container is limited to, and it shares that container's 1GiB with uvicorn and, until
# this was fixed, the whole uploaded file held in memory.

def test_video_transcode_bounds_its_thread_pool(monkeypatch):
    from app.core import media_processing
    from app.core.config import settings

    captured: list[list[str]] = []
    monkeypatch.setattr(media_processing, "_run_ffmpeg", lambda args: captured.append(args))
    # Force the slow path; the remux fast path doesn't encode and so isn't the memory risk.
    monkeypatch.setattr(media_processing, "_remux_if_already_web_ready", lambda i, o: False)

    media_processing.compress_video("in.mov", "out.mp4")

    args = captured[0]
    assert args.count("-threads") == 2, "decoder and encoder each need bounding"
    assert all(args[i + 1] == str(settings.FFMPEG_THREADS) for i, a in enumerate(args) if a == "-threads")
    assert "-filter_threads" in args, "the scale filter keeps its own pool"


def test_audio_and_photo_transcodes_bound_their_thread_pools(monkeypatch):
    from app.core import media_processing

    captured: list[list[str]] = []
    monkeypatch.setattr(media_processing, "_run_ffmpeg", lambda args: captured.append(args))

    media_processing.compress_audio("in.mov", "out.m4a")
    media_processing.compress_photo("in.jpg", "out.jpg")

    for args in captured:
        assert "-threads" in args


def test_uploads_are_streamed_to_disk_not_read_into_memory():
    """The upload routes must not materialise a whole file in RAM before ffmpeg runs.

    Enforced by reading the source: a 150MB upload buffered whole is a large slice of a 1GiB
    container, and it lands exactly when ffmpeg is about to need its own working set.
    """
    from pathlib import Path

    routes = Path(__file__).resolve().parent.parent / "app" / "api" / "routes"
    offenders = [
        p.name
        for p in routes.glob("*.py")
        if "out.write(file.file.read())" in p.read_text(encoding="utf-8")
        or "out.write(upload.file.read())" in p.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"these routes still buffer the whole upload: {offenders}"

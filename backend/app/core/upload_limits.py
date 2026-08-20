"""Per-tier caps on uploaded media.

Two separate dials, because they buy different things:

* **Duration** is what recurring bandwidth costs are made of -- every view of a clip re-pays for
  its whole length. This is the one that scales with traffic.
* **Size** is a one-off: it bounds how much CPU a single upload can burn in ffmpeg before the
  file is compressed down to the serving bitrate.

Free stays at the 30s the platform has always had, so nothing regresses for existing talent;
Premium buys 2 minutes, which is a full monologue or song rather than a snippet. The *number*
of portfolio items is capped separately by FREE_TIER_MEDIA_LIMIT -- that's the primary
free/premium lever, deliberately, since a short cap on length makes the free product bad at its
one job while a cap on count leaves it complete but bounded.
"""
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.media_processing import MediaProcessingError, MediaProcessingTimeout

PREMIUM_TIER = "premium"


def max_video_duration_for(tier: str | None) -> int:
    if tier == PREMIUM_TIER:
        return settings.PREMIUM_MAX_VIDEO_DURATION_SECONDS
    return settings.MAX_VIDEO_DURATION_SECONDS


def max_upload_size_for(tier: str | None) -> int:
    if tier == PREMIUM_TIER:
        return settings.PREMIUM_MAX_UPLOAD_SIZE_BYTES
    return settings.MAX_UPLOAD_SIZE_BYTES


def enforce_upload_size(size: int, tier: str | None) -> None:
    limit = max_upload_size_for(tier)
    if size <= limit:
        return
    upgrade_hint = (
        ""
        if tier == PREMIUM_TIER
        else f" Premium accounts can upload up to {settings.PREMIUM_MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
    )
    raise HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail=f"File is too large (max {limit // (1024 * 1024)}MB).{upgrade_hint}",
    )


def enforce_video_duration(duration: float, tier: str | None) -> None:
    limit = max_video_duration_for(tier)
    if duration <= limit:
        return
    upgrade_hint = (
        ""
        if tier == PREMIUM_TIER
        else f" Premium accounts can upload videos up to {settings.PREMIUM_MAX_VIDEO_DURATION_SECONDS // 60} minutes long."
    )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Videos must be {limit} seconds or shorter (this one is {int(duration)}s).{upgrade_hint}",
    )


def media_processing_http_error(exc: MediaProcessingError, *, noun: str = "file") -> HTTPException:
    """Turn an ffmpeg failure into the right 400 for the user.

    A timeout is our resource limit, not their mistake -- telling someone their perfectly good
    video is invalid when we simply ran out of CPU sends them off to re-export it for nothing.
    The underlying ffmpeg stderr is already logged by media_processing; it is deliberately not
    echoed to the client, since it leaks paths and tool internals.
    """
    if isinstance(exc, MediaProcessingTimeout):
        detail = (
            f"This {noun} took too long for us to process. Try a shorter clip, or export it at a "
            "smaller size — 720p is plenty for an audition."
        )
    else:
        detail = f"Could not process this {noun} — make sure it's a valid video/audio file."
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

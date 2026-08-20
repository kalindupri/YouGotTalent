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

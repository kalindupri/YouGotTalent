"""Compresses uploaded video/audio via ffmpeg before it's stored, to keep Azure Blob storage
and egress costs down. Requires the ffmpeg binary (installed in the backend Docker image).
"""
import json
import logging
import re
import subprocess

from app.core.config import settings

logger = logging.getLogger(__name__)

# Derived from the longest clip we accept rather than hardcoded, so raising a duration cap can
# never silently leave uploads timing out. The multiplier is deliberately generous: the API runs
# on 0.5 vCPU in Azure, where a detailed 1080p source transcodes at roughly real time or worse,
# and formats like ProRes cost more again to decode.
COMPRESS_TIMEOUT_SECONDS = max(300, settings.PREMIUM_MAX_VIDEO_DURATION_SECONDS * 6)

# Applied to decode and encode separately: -threads before -i bounds the decoder, -threads
# before the output bounds the encoder. Both matter -- a 10-bit 4:2:2 source decodes into
# ~8MB frames, so the decoder's buffers are as expensive as x264's.
_THREADS = ["-threads", str(settings.FFMPEG_THREADS)]


class MediaProcessingError(Exception):
    pass


class MediaProcessingTimeout(MediaProcessingError):
    """Ran out of time rather than hitting anything wrong with the file.

    Kept distinct so the user isn't told their perfectly good video is invalid when what
    actually happened is that our own CPU budget ran out.
    """


def probe_video_duration(path: str) -> float:
    """Reads a video's duration in seconds, without transcoding it — used to reject overlong
    uploads before spending time compressing them.

    Tries the container's own duration metadata first (fast, no decoding). Some mobile browsers'
    MediaRecorder output has no duration atom at all (the container is finalized without one,
    even though the audio itself decodes and plays back fine) -- ffprobe returns nothing for
    those, which used to surface as "Could not process this recording" for real, valid mobile
    takes. Falling back to a full decode (ffmpeg reports the actual elapsed time it decoded,
    regardless of container metadata) handles that case.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True,
            timeout=COMPRESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise MediaProcessingTimeout("Could not read this video's duration") from exc

    if result.returncode == 0:
        try:
            return float(result.stdout.decode().strip())
        except ValueError:
            pass

    return _probe_duration_by_decoding(path)


def _probe_duration_by_decoding(path: str) -> float:
    try:
        result = subprocess.run(
            ["ffmpeg", *_THREADS, "-i", path, "-f", "null", "-"],
            capture_output=True,
            timeout=COMPRESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise MediaProcessingTimeout("Could not read this video's duration") from exc

    stderr = result.stderr.decode(errors="replace")
    matches = re.findall(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
    if not matches:
        raise MediaProcessingError("Could not read this video's duration")
    hours, minutes, seconds = matches[-1]
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


# A source at or under these is already fine to serve as-is -- re-encoding it would burn a
# minute of CPU to produce a file no smaller. Matches the transcode targets below.
_REMUX_MAX_WIDTH = 1280
_REMUX_MAX_BITRATE = 1_800_000


def _stream_info(path: str) -> dict:
    """Parsed ffprobe output: the first video stream, the first audio stream, and container
    format. Returns {} if the probe fails for any reason -- callers treat that as "just
    transcode it".

    JSON output rather than the flat key=value form: ffprobe emits `codec_name` *before*
    `codec_type`, so a line-by-line parse has no reliable way to tell which stream a field
    belongs to and silently attributes the audio codec to the video stream.
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
            capture_output=True,
            timeout=COMPRESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {}
    if result.returncode != 0:
        return {}

    try:
        parsed = json.loads(result.stdout.decode(errors="replace"))
    except ValueError:
        return {}

    streams = parsed.get("streams") or []
    return {
        "video": next((s for s in streams if s.get("codec_type") == "video"), None),
        "audio": next((s for s in streams if s.get("codec_type") == "audio"), None),
        "format": parsed.get("format") or {},
    }


def _remux_if_already_web_ready(input_path: str, output_path: str) -> bool:
    """Stream-copies instead of re-encoding when the source is already H.264/AAC at our target
    size. Returns True if it did.

    A full transcode of a 30-second 1080p clip costs ~35s on the 0.5 vCPU the app runs with in
    Azure -- the whole time spent inside the upload request, with the user watching a spinner.
    Anything already conformant (notably the in-app recorder's own output, and most re-shared
    clips) skips that entirely; remuxing is I/O-bound and finishes in about a second.
    """
    info = _stream_info(input_path)
    video = info.get("video")
    if not video or video.get("codec_name") != "h264":
        return False
    audio = info.get("audio")
    # No audio track at all is fine; anything other than AAC would need re-encoding.
    if audio is not None and audio.get("codec_name") != "aac":
        return False
    try:
        if int(video.get("width") or 0) > _REMUX_MAX_WIDTH:
            return False
        # Stream bitrate is absent in some containers; the format-level figure is a fine stand-in.
        bitrate = int(video.get("bit_rate") or info["format"].get("bit_rate") or 0)
    except (TypeError, ValueError):
        return False
    if bitrate == 0 or bitrate > _REMUX_MAX_BITRATE:
        return False

    try:
        _run_ffmpeg(["-i", input_path, "-c", "copy", "-movflags", "+faststart", output_path])
    except MediaProcessingError:
        # Not every conformant-looking stream remuxes cleanly into mp4 -- fall back rather than
        # failing the upload. _run_ffmpeg already logged the reason at warning level.
        logger.info("remux fast path declined for %s; falling back to a full transcode", input_path)
        return False
    return True


def compress_video(input_path: str, output_path: str) -> None:
    if _remux_if_already_web_ready(input_path, output_path):
        return
    _run_ffmpeg(
        [
            *_THREADS,
            "-i", input_path,
            # Downscale anything wider than 1280px; never upscale. -2 keeps height even (required
            # by libx264's yuv420p).
            "-vf", "scale='min(1280,iw)':-2",
            # Bounds the scale filter's own worker pool, which is separate from -threads.
            "-filter_threads", str(settings.FFMPEG_THREADS),
            *_THREADS,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "26",
            "-maxrate", "1500k",
            "-bufsize", "3000k",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path,
        ]
    )


def compress_audio(input_path: str, output_path: str) -> None:
    _run_ffmpeg([*_THREADS, "-i", input_path, "-vn", *_THREADS, "-c:a", "aac", "-b:a", "128k", output_path])


def compress_photo(input_path: str, output_path: str) -> None:
    _run_ffmpeg(
        [
            *_THREADS,
            "-i", input_path,
            # Downscale anything wider than 1600px; never upscale.
            "-vf", "scale='min(1600,iw)':-1",
            "-filter_threads", str(settings.FFMPEG_THREADS),
            *_THREADS,
            "-q:v", "4",
            output_path,
        ]
    )


def _run_ffmpeg(args: list[str]) -> None:
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", *args],
            capture_output=True,
            timeout=COMPRESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        logger.warning("ffmpeg timed out after %ss: %s", COMPRESS_TIMEOUT_SECONDS, " ".join(args))
        raise MediaProcessingTimeout("Processing this file took too long") from exc

    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace")[-2000:]
        if result.returncode < 0:
            logger.error(
                "ffmpeg was killed by signal %s (most likely the OOM killer -- check the "
                "container memory limit against FFMPEG_THREADS): %s",
                -result.returncode,
                " ".join(args),
            )
        # Logged here rather than at the call sites, which catch MediaProcessingError to build a
        # user-facing message and would otherwise discard the only explanation of what failed.
        logger.warning(
            "ffmpeg exited %s | args: %s | stderr: %s", result.returncode, " ".join(args), stderr
        )
        raise MediaProcessingError(stderr)

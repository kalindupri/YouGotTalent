"""Compresses uploaded video/audio via ffmpeg before it's stored, to keep Azure Blob storage
and egress costs down. Requires the ffmpeg binary (installed in the backend Docker image).
"""
import re
import subprocess

COMPRESS_TIMEOUT_SECONDS = 180


class MediaProcessingError(Exception):
    pass


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
        raise MediaProcessingError("Could not read this video's duration") from exc

    if result.returncode == 0:
        try:
            return float(result.stdout.decode().strip())
        except ValueError:
            pass

    return _probe_duration_by_decoding(path)


def _probe_duration_by_decoding(path: str) -> float:
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", path, "-f", "null", "-"],
            capture_output=True,
            timeout=COMPRESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise MediaProcessingError("Could not read this video's duration") from exc

    stderr = result.stderr.decode(errors="replace")
    matches = re.findall(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
    if not matches:
        raise MediaProcessingError("Could not read this video's duration")
    hours, minutes, seconds = matches[-1]
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def compress_video(input_path: str, output_path: str) -> None:
    _run_ffmpeg(
        [
            "-i", input_path,
            # Downscale anything wider than 1280px; never upscale. -2 keeps height even (required
            # by libx264's yuv420p).
            "-vf", "scale='min(1280,iw)':-2",
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
    _run_ffmpeg(["-i", input_path, "-vn", "-c:a", "aac", "-b:a", "128k", output_path])


def compress_photo(input_path: str, output_path: str) -> None:
    _run_ffmpeg(
        [
            "-i", input_path,
            # Downscale anything wider than 1600px; never upscale.
            "-vf", "scale='min(1600,iw)':-1",
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
        raise MediaProcessingError("Processing this file took too long") from exc

    if result.returncode != 0:
        raise MediaProcessingError(result.stderr.decode(errors="replace")[-2000:])

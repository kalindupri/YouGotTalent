"""Compresses uploaded video/audio via ffmpeg before it's stored, to keep Azure Blob storage
and egress costs down. Requires the ffmpeg binary (installed in the backend Docker image).
"""
import subprocess

COMPRESS_TIMEOUT_SECONDS = 180


class MediaProcessingError(Exception):
    pass


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

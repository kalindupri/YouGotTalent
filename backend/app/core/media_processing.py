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


def mix_vocal_with_instrumental(
    vocal_path: str,
    instrumental_path: str,
    output_path: str,
    bass_db: float = 0.0,
    mid_db: float = 0.0,
    treble_db: float = 0.0,
    reverb_amount: float = 0.0,
    delay_ms: float = 0.0,
    delay_feedback: float = 0.0,
    vocal_gain_db: float = 0.0,
    sync_offset_ms: float = 0.0,
) -> None:
    """Applies 3-band EQ + reverb + delay + gain to the talent's recorded vocal (matching
    whatever they dialed in on the live client-side preview -- see AudioAuditionRecorder.tsx),
    optionally nudges it earlier/later relative to the instrumental to fix sync drift, and mixes
    it onto the instrumental. Output duration follows the instrumental (duration=first), since
    that's the backing track the talent sang along to.

    All effect params default to "off" (flat EQ, no reverb/delay, no gain/offset change) --
    unlike the original fixed version of this function, nothing is forced on unless the talent
    actually dialed it in.
    """
    reverb_amount = max(0.0, min(100.0, reverb_amount)) / 100.0
    delay_feedback = max(0.0, min(60.0, delay_feedback)) / 100.0
    delay_ms = max(0.0, min(500.0, delay_ms))
    vocal_gain_db = max(-12.0, min(12.0, vocal_gain_db))
    sync_offset_ms = max(-1000.0, min(1000.0, sync_offset_ms))

    # aecho can't take a literal 0 decay, so floor it -- at this level the tap is inaudible,
    # which is how "reverb/delay off" is represented here.
    reverb_decay = max(reverb_amount * 0.6, 0.001)
    reverb_tap_ms = int(400 + reverb_amount * 800)
    delay_decay = max(delay_feedback, 0.001)
    delay_tap_ms = max(int(delay_ms), 1)

    # A flat dB boost alone isn't reliable -- a quiet raw mic recording still sounds buried next
    # to a mastered instrumental even after boosting it, and a hot one can clip. loudnorm brings
    # the vocal to a consistent, present loudness first regardless of how quiet/loud the source
    # recording was; vocal_gain_db then applies on top of that as the talent's own adjustment.
    vocal_filter = (
        f"loudnorm=I=-16:TP=-1.5:LRA=11,"
        f"volume={vocal_gain_db}dB,"
        f"bass=g={bass_db},treble=g={treble_db},equalizer=f=1000:width_type=o:width=2:g={mid_db},"
        f"aecho=0.8:{0.3 + reverb_amount * 0.5:.3f}:{reverb_tap_ms}:{reverb_decay:.3f},"
        f"aecho=0.8:{delay_decay:.3f}:{delay_tap_ms}:{delay_decay:.3f}"
    )

    # A positive offset means the vocal was sung/recorded *behind* the instrumental (needs to
    # catch up), so delay the instrumental to meet it; negative means the vocal is ahead, so
    # delay the vocal instead. There's no audio to pull from before the recording started, which
    # is why this is two one-sided delays rather than a single signed shift on one stream.
    instrumental_delay_ms = max(int(-sync_offset_ms), 0)
    vocal_delay_ms = max(int(sync_offset_ms), 0)
    if vocal_delay_ms:
        vocal_filter += f",adelay={vocal_delay_ms}:all=1"
    instrumental_filter = f"adelay={instrumental_delay_ms}:all=1" if instrumental_delay_ms else "anull"

    # normalize=0 keeps the vocal's dialed-in volume intact instead of amix's default of
    # halving both streams to guarantee no clipping; alimiter is the safety net for that instead.
    filter_complex = (
        f"[0:a]{instrumental_filter}[inst_fx];"
        f"[1:a]{vocal_filter}[vocal_fx];"
        f"[inst_fx][vocal_fx]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[mixed];"
        f"[mixed]alimiter=limit=0.95[out]"
    )

    _run_ffmpeg(
        [
            "-i", instrumental_path,
            "-i", vocal_path,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "aac",
            "-b:a", "128k",
            output_path,
        ]
    )


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

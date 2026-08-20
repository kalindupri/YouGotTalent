"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ApiError, CastingCallRole, UploadProgress, api } from "@/lib/api";
import UploadProgressBar from "@/components/UploadProgressBar";
import { btnPrimary, btnSecondary } from "@/lib/ui";

const MAX_RECORDING_SECONDS = 30;

// iOS/macOS Safari's MediaRecorder doesn't support WebM at all -- it records to MP4/AAC
// instead. Picking (and remembering) whichever format the browser actually supports, rather
// than hardcoding "audio/webm", is what makes recording work on both platforms: labeling a
// Safari-recorded MP4 blob as "audio/webm" produced a file no player could decode.
function pickSupportedMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return undefined;
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/mp4;codecs=mp4a.40.2", "audio/aac"];
  return candidates.find((c) => MediaRecorder.isTypeSupported(c));
}

export default function AudioAuditionRecorder({
  role,
  castingCallId,
  token,
  onSubmissionReady,
}: {
  role: CastingCallRole;
  castingCallId: string;
  token: string;
  onSubmissionReady: (url: string) => void;
}) {
  const [recording, setRecording] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(MAX_RECORDING_SECONDS);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [micLevel, setMicLevel] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const guideAudioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const micSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const micAnalyserRef = useRef<AnalyserNode | null>(null);
  const micMeterFrameRef = useRef<number | null>(null);

  const takeUrl = useMemo(() => (recordedBlob ? URL.createObjectURL(recordedBlob) : null), [recordedBlob]);
  useEffect(() => {
    return () => {
      if (takeUrl) URL.revokeObjectURL(takeUrl);
    };
  }, [takeUrl]);

  function getAudioContext(): AudioContext {
    if (!audioContextRef.current) {
      const Ctor = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      audioContextRef.current = new Ctor();
    }
    const ctx = audioContextRef.current;
    if (ctx.state === "suspended") ctx.resume().catch(() => {});
    return ctx;
  }

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (micMeterFrameRef.current) cancelAnimationFrame(micMeterFrameRef.current);
      mediaRecorderRef.current?.stream.getTracks().forEach((t) => t.stop());
      audioContextRef.current?.close().catch(() => {});
    };
  }, []);

  function startMicMeter(stream: MediaStream) {
    const ctx = getAudioContext();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    // Deliberately NOT connected onward to ctx.destination -- this tap is for the level
    // meter only, connecting it to output would create a feedback loop through the speakers.
    source.connect(analyser);
    micSourceRef.current = source;
    micAnalyserRef.current = analyser;

    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteTimeDomainData(data);
      let sumSquares = 0;
      for (let i = 0; i < data.length; i++) {
        const v = (data[i] - 128) / 128;
        sumSquares += v * v;
      }
      const rms = Math.sqrt(sumSquares / data.length);
      setMicLevel(Math.min(100, Math.round(rms * 350)));
      micMeterFrameRef.current = requestAnimationFrame(tick);
    };
    micMeterFrameRef.current = requestAnimationFrame(tick);
  }

  function stopMicMeter() {
    if (micMeterFrameRef.current) cancelAnimationFrame(micMeterFrameRef.current);
    micMeterFrameRef.current = null;
    micSourceRef.current?.disconnect();
    micAnalyserRef.current?.disconnect();
    micSourceRef.current = null;
    micAnalyserRef.current = null;
    setMicLevel(0);
  }

  async function startRecording() {
    setError(null);
    setRecordedBlob(null);
    setUploadedUrl(null);
    try {
      // Deliberately no explicit echoCancellation/noiseSuppression/autoGainControl constraints
      // here -- forcing them on was tried and made a real headphone-wearing test recording come
      // out at -63dB mean volume (near silence/noise-floor only), likely from Chrome's forced
      // WebRTC processing conflicting with this machine's OS-level audio driver enhancements.
      // Bare {audio: true} lets the browser + OS pick sane defaults, which is the more broadly
      // compatible path across devices.
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = pickSupportedMimeType();
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        setRecordedBlob(new Blob(chunksRef.current, { type: mimeType ?? recorder.mimeType ?? "audio/webm" }));
        stream.getTracks().forEach((t) => t.stop());
        stopMicMeter();
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setSecondsLeft(MAX_RECORDING_SECONDS);
      startMicMeter(stream);

      // The guide track has its own player for previewing the song beforehand -- if it was left
      // playing (or gets started mid-recording) it plays through the speakers right alongside
      // recording, and the mic picks up its vocals too. Force it silent here.
      if (guideAudioRef.current) {
        guideAudioRef.current.pause();
        guideAudioRef.current.currentTime = 0;
      }

      timerRef.current = setInterval(() => {
        setSecondsLeft((s) => {
          if (s <= 1) {
            stopRecording();
            return 0;
          }
          return s - 1;
        });
      }, 1000);
    } catch {
      setError("Couldn't access your microphone — check your browser permissions.");
    }
  }

  function stopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  function reRecord() {
    setRecordedBlob(null);
    setUploadedUrl(null);
    setError(null);
  }

  async function handleSubmit() {
    if (!recordedBlob) return;
    setUploading(true);
    setError(null);
    setProgress(null);
    try {
      const { url } = await api.uploadAuditionRecording(castingCallId, role.id, recordedBlob, token, setProgress);
      setUploadedUrl(url);
      onSubmissionReady(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit your recording.");
    } finally {
      setUploading(false);
      setProgress(null);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div>
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Guided audition</p>
        <p className="mt-0.5 text-xs text-zinc-500">
          Listen to the guide track to learn the song, then record your own voice clip (up to {MAX_RECORDING_SECONDS}s)
          and submit it.
        </p>
      </div>

      {role.guide_track_url && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-bold uppercase tracking-wide text-zinc-500">Guide track</span>
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <audio
            ref={guideAudioRef}
            controls
            src={role.guide_track_url}
            className="w-full"
            onPlay={() => {
              // Guards against starting the guide track *during* an active recording (e.g. the
              // user clicks play on it mid-take) -- same bleed-into-the-mic problem as above.
              if (recording) guideAudioRef.current?.pause();
            }}
          />
        </div>
      )}

      {!recordedBlob && !recording && (
        <button type="button" onClick={startRecording} className={`w-fit ${btnPrimary}`}>
          Record your take
        </button>
      )}

      {recording && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <span className="flex h-3 w-3 animate-pulse rounded-full bg-rose-600" />
            <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Recording… {secondsLeft}s left</span>
            <button type="button" onClick={stopRecording} className={btnSecondary}>
              Stop
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wide text-zinc-500">Mic level</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
              <div
                className={`h-full rounded-full transition-[width] duration-75 ${
                  micLevel > 80 ? "bg-amber-500" : "bg-emerald-500"
                }`}
                style={{ width: `${micLevel}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {recordedBlob && (
        <div className="flex flex-col gap-3">
          <div>
            <span className="text-xs font-bold uppercase tracking-wide text-zinc-500">Your take</span>
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <audio controls src={takeUrl ?? undefined} className="w-full" />
          </div>

          <div className="flex gap-2">
            <button type="button" onClick={handleSubmit} disabled={uploading} className={btnPrimary}>
              {uploading ? "Submitting…" : uploadedUrl ? "Submitted" : "Use this recording"}
            </button>
            <UploadProgressBar progress={progress} />
            <button type="button" onClick={reRecord} className={btnSecondary}>
              Re-record
            </button>
          </div>

          {uploadedUrl && (
            <p className="text-xs font-medium text-emerald-600">
              Your recording is ready — add an optional message below and click Apply to submit.
            </p>
          )}
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}

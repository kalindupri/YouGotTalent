"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, CastingCallRole, api } from "@/lib/api";
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
  onMixed,
}: {
  role: CastingCallRole;
  castingCallId: string;
  token: string;
  onMixed: (url: string) => void;
}) {
  const [recording, setRecording] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(MAX_RECORDING_SECONDS);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [mixing, setMixing] = useState(false);
  const [mixedUrl, setMixedUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const instrumentalAudioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      mediaRecorderRef.current?.stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  async function startRecording() {
    setError(null);
    setRecordedBlob(null);
    setMixedUrl(null);
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
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setSecondsLeft(MAX_RECORDING_SECONDS);

      instrumentalAudioRef.current?.play().catch(() => {});

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
    instrumentalAudioRef.current?.pause();
    if (instrumentalAudioRef.current) instrumentalAudioRef.current.currentTime = 0;
    setRecording(false);
  }

  function reRecord() {
    setRecordedBlob(null);
    setMixedUrl(null);
    setError(null);
  }

  async function handleMix() {
    if (!recordedBlob) return;
    setMixing(true);
    setError(null);
    try {
      const { url } = await api.mixAuditionRecording(castingCallId, role.id, recordedBlob, token);
      setMixedUrl(url);
      onMixed(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not mix your recording.");
    } finally {
      setMixing(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div>
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Guided audition</p>
        <p className="mt-0.5 text-xs text-zinc-500">
          Listen to the guide track to learn the song, then record yourself singing along to the instrumental
          (up to {MAX_RECORDING_SECONDS}s).
        </p>
        <p className="mt-1 text-xs font-medium text-amber-600 dark:text-amber-400">
          Use headphones/earphones while recording — without them, your mic can pick up the
          instrumental from your speakers and turn your recording into static.
        </p>
      </div>

      {role.guide_track_url && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-bold uppercase tracking-wide text-zinc-500">Guide track</span>
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <audio controls src={role.guide_track_url} className="w-full" />
        </div>
      )}

      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio ref={instrumentalAudioRef} src={role.instrumental_track_url ?? undefined} className="hidden" />

      {!recordedBlob && !recording && (
        <button type="button" onClick={startRecording} className={`w-fit ${btnPrimary}`}>
          Record your take
        </button>
      )}

      {recording && (
        <div className="flex items-center gap-3">
          <span className="flex h-3 w-3 animate-pulse rounded-full bg-rose-600" />
          <span className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">Recording… {secondsLeft}s left</span>
          <button type="button" onClick={stopRecording} className={btnSecondary}>
            Stop
          </button>
        </div>
      )}

      {recordedBlob && !mixedUrl && (
        <div className="flex flex-col gap-2">
          <span className="text-xs font-bold uppercase tracking-wide text-zinc-500">Your take</span>
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <audio controls src={URL.createObjectURL(recordedBlob)} className="w-full" />
          <div className="flex gap-2">
            <button type="button" onClick={handleMix} disabled={mixing} className={btnPrimary}>
              {mixing ? "Mixing…" : "Mix with instrumental"}
            </button>
            <button type="button" onClick={reRecord} className={btnSecondary}>
              Re-record
            </button>
          </div>
        </div>
      )}

      {mixedUrl && (
        <div className="flex flex-col gap-2">
          <span className="text-xs font-bold uppercase tracking-wide text-emerald-600">Your mixed audition</span>
          {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
          <audio controls src={mixedUrl} className="w-full" />
          <button type="button" onClick={reRecord} className={`w-fit ${btnSecondary}`}>
            Re-record
          </button>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}

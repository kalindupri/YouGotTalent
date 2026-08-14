"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ApiError, CastingCallRole, api } from "@/lib/api";
import { btnPrimary, btnSecondary } from "@/lib/ui";
import Knob from "@/components/Knob";

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
  const [micLevel, setMicLevel] = useState(0);

  const [bassDb, setBassDb] = useState(0);
  const [midDb, setMidDb] = useState(0);
  const [trebleDb, setTrebleDb] = useState(0);
  const [reverbAmount, setReverbAmount] = useState(0);
  const [delayAmount, setDelayAmount] = useState(0);
  const [vocalGainDb, setVocalGainDb] = useState(0);
  const [syncOffsetMs, setSyncOffsetMs] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const guideAudioRef = useRef<HTMLAudioElement | null>(null);
  const instrumentalAudioRef = useRef<HTMLAudioElement | null>(null);
  const takeAudioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const micSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const micAnalyserRef = useRef<AnalyserNode | null>(null);
  const micMeterFrameRef = useRef<number | null>(null);

  // Live client-side preview graph for "Your take" -- rebuilt whenever a fresh recording is
  // made, since createMediaElementSource can only ever be called once per <audio> element.
  const eqNodesRef = useRef<{ bass: BiquadFilterNode; mid: BiquadFilterNode; treble: BiquadFilterNode } | null>(null);
  const reverbWetRef = useRef<GainNode | null>(null);
  const delayNodeRef = useRef<DelayNode | null>(null);
  const delayFeedbackRef = useRef<GainNode | null>(null);
  const delayWetRef = useRef<GainNode | null>(null);
  const vocalGainRef = useRef<GainNode | null>(null);

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
        stopMicMeter();
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setSecondsLeft(MAX_RECORDING_SECONDS);
      startMicMeter(stream);

      // The guide track has its own player for previewing the song beforehand -- if it was left
      // playing (or gets started mid-recording) it plays through the speakers right alongside the
      // instrumental, and the mic picks up its reference vocals too. Force it silent here.
      if (guideAudioRef.current) {
        guideAudioRef.current.pause();
        guideAudioRef.current.currentTime = 0;
      }
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
    setBassDb(0);
    setMidDb(0);
    setTrebleDb(0);
    setReverbAmount(0);
    setDelayAmount(0);
    setVocalGainDb(0);
    setSyncOffsetMs(0);
  }

  // Builds the live-preview effects graph for "Your take" once its <audio> element exists.
  // No impulse-response file for the reverb -- a small feedback-delay network (a handful of
  // short, staggered taps with damping) keeps the frontend self-contained.
  useEffect(() => {
    if (!recordedBlob || !takeAudioRef.current) return;
    const ctx = getAudioContext();
    const source = ctx.createMediaElementSource(takeAudioRef.current);

    const vocalGain = ctx.createGain();
    vocalGain.gain.value = 1;

    const bass = ctx.createBiquadFilter();
    bass.type = "lowshelf";
    bass.frequency.value = 200;
    const mid = ctx.createBiquadFilter();
    mid.type = "peaking";
    mid.frequency.value = 1000;
    mid.Q.value = 1;
    const treble = ctx.createBiquadFilter();
    treble.type = "highshelf";
    treble.frequency.value = 4000;

    source.connect(vocalGain);
    vocalGain.connect(bass);
    bass.connect(mid);
    mid.connect(treble);
    treble.connect(ctx.destination);

    const reverbWet = ctx.createGain();
    reverbWet.gain.value = 0;
    [0.029, 0.037, 0.053].forEach((tapSeconds) => {
      const tapDelay = ctx.createDelay(1);
      tapDelay.delayTime.value = tapSeconds;
      const tapFeedback = ctx.createGain();
      tapFeedback.gain.value = 0.35;
      const damping = ctx.createBiquadFilter();
      damping.type = "lowpass";
      damping.frequency.value = 3500;
      treble.connect(tapDelay);
      tapDelay.connect(damping);
      damping.connect(tapFeedback);
      tapFeedback.connect(tapDelay);
      damping.connect(reverbWet);
    });
    reverbWet.connect(ctx.destination);

    const delayNode = ctx.createDelay(1);
    delayNode.delayTime.value = 0.001;
    const delayFeedback = ctx.createGain();
    delayFeedback.gain.value = 0;
    const delayWet = ctx.createGain();
    delayWet.gain.value = 0;
    treble.connect(delayNode);
    delayNode.connect(delayFeedback);
    delayFeedback.connect(delayNode);
    delayNode.connect(delayWet);
    delayWet.connect(ctx.destination);

    eqNodesRef.current = { bass, mid, treble };
    reverbWetRef.current = reverbWet;
    delayNodeRef.current = delayNode;
    delayFeedbackRef.current = delayFeedback;
    delayWetRef.current = delayWet;
    vocalGainRef.current = vocalGain;

    return () => {
      source.disconnect();
      vocalGain.disconnect();
      bass.disconnect();
      mid.disconnect();
      treble.disconnect();
      reverbWet.disconnect();
      delayNode.disconnect();
      delayFeedback.disconnect();
      delayWet.disconnect();
      eqNodesRef.current = null;
      reverbWetRef.current = null;
      delayNodeRef.current = null;
      delayFeedbackRef.current = null;
      delayWetRef.current = null;
      vocalGainRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordedBlob]);

  // Updates the live graph instantly as knobs move -- no server round-trip. The same values
  // are sent to the backend on "Mix with instrumental" so the final render matches this preview.
  useEffect(() => {
    const eq = eqNodesRef.current;
    if (eq) {
      eq.bass.gain.value = bassDb;
      eq.mid.gain.value = midDb;
      eq.treble.gain.value = trebleDb;
    }
    if (reverbWetRef.current) reverbWetRef.current.gain.value = (reverbAmount / 100) * 0.6;
    if (delayNodeRef.current) delayNodeRef.current.delayTime.value = Math.max((delayAmount / 100) * 0.4, 0.001);
    if (delayFeedbackRef.current) delayFeedbackRef.current.gain.value = (delayAmount / 100) * 0.35;
    if (delayWetRef.current) delayWetRef.current.gain.value = delayAmount > 0 ? Math.min((delayAmount / 100) * 0.5, 0.5) : 0;
    if (vocalGainRef.current) vocalGainRef.current.gain.value = Math.pow(10, vocalGainDb / 20);
  }, [bassDb, midDb, trebleDb, reverbAmount, delayAmount, vocalGainDb]);

  async function handleMix() {
    if (!recordedBlob) return;
    setMixing(true);
    setError(null);
    try {
      const { url } = await api.mixAuditionRecording(castingCallId, role.id, recordedBlob, token, {
        bassDb,
        midDb,
        trebleDb,
        reverbAmount,
        delayMs: (delayAmount / 100) * 400,
        delayFeedback: (delayAmount / 100) * 50,
        vocalGainDb,
        syncOffsetMs,
      });
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

      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <audio ref={instrumentalAudioRef} src={role.instrumental_track_url ?? undefined} className="hidden" />

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

      {recordedBlob && !mixedUrl && (
        <div className="flex flex-col gap-3">
          <div>
            <span className="text-xs font-bold uppercase tracking-wide text-zinc-500">Your take</span>
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <audio ref={takeAudioRef} controls src={takeUrl ?? undefined} className="w-full" />
          </div>

          <div className="flex flex-wrap items-end gap-4 rounded-md bg-zinc-50 p-3 dark:bg-zinc-900/50">
            <Knob label="Volume" value={vocalGainDb} min={-12} max={12} step={1} unit="dB" onChange={setVocalGainDb} />
            <Knob label="Sync" value={syncOffsetMs} min={-1000} max={1000} step={25} unit="ms" onChange={setSyncOffsetMs} />
            <Knob label="Bass" value={bassDb} min={-12} max={12} step={1} unit="dB" onChange={setBassDb} />
            <Knob label="Mid" value={midDb} min={-12} max={12} step={1} unit="dB" onChange={setMidDb} />
            <Knob label="Treble" value={trebleDb} min={-12} max={12} step={1} unit="dB" onChange={setTrebleDb} />
            <Knob label="Reverb" value={reverbAmount} min={0} max={100} step={5} unit="%" onChange={setReverbAmount} />
            <Knob label="Delay" value={delayAmount} min={0} max={100} step={5} unit="%" onChange={setDelayAmount} />
          </div>
          <p className="text-[11px] text-zinc-500">
            Sync shifts your vocal earlier (−) or later (+) to line it up with the instrumental if the take drifted
            out of time.
          </p>

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

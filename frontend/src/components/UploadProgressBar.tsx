"use client";

import type { UploadProgress } from "@/lib/api";

/** Progress readout for a file upload.
 *
 * Two phases, because an upload has two waits and only the first one has a percentage. Once the
 * bytes are sent the server still has to compress the file with ffmpeg — on a 30-second 1080p
 * clip that is another ~35 seconds on the CPU the API runs with. A bar frozen at 100% reads as
 * a hang, so the second phase says what is actually happening and animates instead of counting.
 */
export default function UploadProgressBar({ progress }: { progress: UploadProgress | null }) {
  if (!progress) return null;

  const processing = progress.phase === "processing";

  return (
    <div className="mt-2" aria-live="polite">
      <div className="mb-1 flex items-center justify-between text-xs font-medium text-zinc-600 dark:text-zinc-400">
        <span>{processing ? "Processing your file…" : "Uploading…"}</span>
        {!processing && <span>{progress.percent}%</span>}
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        // Omitted while processing: the phase has no measurable progress, and an explicit 100
        // would tell a screen reader the work is finished when it isn't.
        aria-valuenow={processing ? undefined : progress.percent}
        aria-label={processing ? "Processing your file" : "Upload progress"}
      >
        {processing ? (
          <div className="h-full w-1/3 animate-[upload-indeterminate_1.2s_ease-in-out_infinite] rounded-full bg-rose-500" />
        ) : (
          <div
            className="h-full rounded-full bg-rose-500 transition-[width] duration-200"
            style={{ width: `${progress.percent}%` }}
          />
        )}
      </div>
      {processing && (
        <p className="mt-1 text-xs text-zinc-500">
          We&apos;re compressing it so it loads fast for talent hunts. This can take up to a minute for
          longer videos — you can leave this page open.
        </p>
      )}
    </div>
  );
}

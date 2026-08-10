"use client";

import { FormEvent, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { btnPrimary, btnSmall, inputClass, labelClass } from "@/lib/ui";

export default function SendOfferForm({
  talentId,
  applicationId,
  token,
  onSent,
  onCancel,
}: {
  talentId: string;
  applicationId: string;
  token: string;
  onSent: () => void;
  onCancel: () => void;
}) {
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      // Bookings are stored and compared as a timezone-naive wall clock (matching the
      // availability windows they're validated against) — send the datetime-local value
      // as-is rather than through `new Date().toISOString()`, which would reinterpret it in
      // the browser's local timezone and silently shift the proposed time.
      await api.requestBooking(
        talentId,
        {
          start_at: `${startAt}:00`,
          end_at: `${endAt}:00`,
          message: message || undefined,
          application_id: applicationId,
        },
        token
      );
      onSent();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send this offer.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-2 rounded-lg border border-zinc-200 p-3 dark:border-zinc-800">
      <label className={labelClass}>
        Proposed start
        <input required type="datetime-local" value={startAt} onChange={(e) => setStartAt(e.target.value)} className={inputClass} />
      </label>
      <label className={labelClass}>
        Proposed end
        <input required type="datetime-local" value={endAt} onChange={(e) => setEndAt(e.target.value)} className={inputClass} />
      </label>
      <label className={labelClass}>
        Terms / message (optional)
        <textarea rows={2} value={message} onChange={(e) => setMessage(e.target.value)} className={inputClass} />
      </label>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={submitting} className={btnPrimary}>
          {submitting ? "Sending…" : "Send offer"}
        </button>
        <button type="button" onClick={onCancel} className={btnSmall}>
          Cancel
        </button>
      </div>
    </form>
  );
}

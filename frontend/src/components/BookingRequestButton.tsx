"use client";

import { useState } from "react";
import { CalendarClock, Check } from "lucide-react";
import { ApiError, AvailabilityWindow, BusyRange, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { DAYS_OF_WEEK, btnSmall, btnSmallPrimary, formatTimeOfDay, inputClass, labelClass } from "@/lib/ui";

export default function BookingRequestButton({ talentId }: { talentId: string }) {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [windows, setWindows] = useState<AvailabilityWindow[]>([]);
  const [busyDates, setBusyDates] = useState<BusyRange[]>([]);
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleOpen() {
    setOpen(true);
    if (windows.length > 0) return;
    setLoading(true);
    try {
      const [availabilityWindows, busy] = await Promise.all([
        api.listTalentAvailability(talentId),
        api.getTalentBusyDates(talentId).catch(() => []),
      ]);
      setWindows(availabilityWindows);
      setBusyDates(busy);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (!token || !date || !startTime || !endTime) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.requestBooking(
        talentId,
        {
          // Sent as a plain local timestamp (no timezone conversion) since availability
          // windows are timezone-naive wall-clock times, not UTC.
          start_at: `${date}T${startTime}:00`,
          end_at: `${date}T${endTime}:00`,
          message: message || undefined,
        },
        token
      );
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send this booking request.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative">
      <button onClick={handleOpen} className={btnSmall}>
        <CalendarClock className="h-3.5 w-3.5" /> Request a booking
      </button>

      {open && (
        <div className="absolute right-0 top-full z-10 mt-2 w-80 rounded-xl border border-zinc-200 bg-white p-4 shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          {sent ? (
            <p className="flex items-center gap-1.5 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
              <Check className="h-4 w-4" /> Request sent — they&apos;ll see it on their dashboard.
            </p>
          ) : loading ? (
            <p className="text-sm text-zinc-500">Loading availability…</p>
          ) : windows.length === 0 ? (
            <p className="text-sm text-zinc-500">This talent hasn&apos;t set their availability yet.</p>
          ) : (
            <div className="flex flex-col gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-zinc-500">Weekly availability</p>
                <ul className="mt-1 flex flex-col gap-0.5 text-sm text-zinc-700 dark:text-zinc-300">
                  {windows.map((w) => (
                    <li key={w.id}>
                      {DAYS_OF_WEEK[w.day_of_week]}: {formatTimeOfDay(w.start_time)} &ndash; {formatTimeOfDay(w.end_time)}
                    </li>
                  ))}
                </ul>
              </div>
              {busyDates.length > 0 && (
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-zinc-500">Already busy</p>
                  <ul className="mt-1 flex flex-col gap-0.5 text-sm text-zinc-700 dark:text-zinc-300">
                    {busyDates.map((r, i) => (
                      <li key={i}>
                        {r.start_date}
                        {r.end_date !== r.start_date ? ` – ${r.end_date}` : ""}
                        {r.title ? ` (${r.title})` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <label className={labelClass}>
                Date
                <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className={inputClass} />
              </label>
              <div className="flex gap-2">
                <label className={labelClass}>
                  Start
                  <input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} className={inputClass} />
                </label>
                <label className={labelClass}>
                  End
                  <input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} className={inputClass} />
                </label>
              </div>
              <label className={labelClass}>
                Message (optional)
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={2}
                  className={inputClass}
                />
              </label>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setOpen(false)} className={btnSmall}>
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={submitting || !date || !startTime || !endTime}
                  className={btnSmallPrimary}
                >
                  {submitting ? "Sending…" : "Send request"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

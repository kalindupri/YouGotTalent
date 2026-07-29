"use client";

import { FormEvent, useState } from "react";
import { Star } from "lucide-react";
import { ApiError, api } from "@/lib/api";
import { btnSmall, inputClass, labelClass } from "@/lib/ui";

export default function BookingReviewForm({
  bookingId,
  token,
  revieweeLabel,
}: {
  bookingId: string;
  token: string;
  revieweeLabel: string;
}) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (done) {
    return <p className="mt-2 text-sm font-semibold text-emerald-700 dark:text-emerald-400">Thanks for your review!</p>;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (rating === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.leaveReview(bookingId, { rating, comment: comment || undefined }, token);
      setDone(true);
    } catch (err) {
      // A 400 here almost always means this booking was already reviewed by this party —
      // treat it the same as a successful submission rather than showing a raw error.
      if (err instanceof ApiError && err.status === 400) {
        setDone(true);
      } else {
        setError("Could not submit your review.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-2 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
      <p className="text-xs font-bold uppercase tracking-wide text-zinc-500">Rate {revieweeLabel}</p>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setRating(n)}
            aria-label={`${n} star${n === 1 ? "" : "s"}`}
            className="text-amber-500"
          >
            <Star className="h-5 w-5" fill={n <= rating ? "currentColor" : "none"} />
          </button>
        ))}
      </div>
      <label className={labelClass}>
        Comment (optional)
        <textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={2} className={inputClass} />
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button type="submit" disabled={submitting || rating === 0} className={`${btnSmall} w-fit`}>
        Submit review
      </button>
    </form>
  );
}

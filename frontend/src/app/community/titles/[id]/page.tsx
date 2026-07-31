"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Star } from "lucide-react";
import { ApiError, Title, TitleReview, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnPrimary, btnSmall, inputClass, sectionClass } from "@/lib/ui";
import ReportButton from "@/components/ReportButton";
import TitlePoster from "@/components/TitlePoster";
import AuthorAvatar from "@/components/AuthorAvatar";

const WORK_TYPE_LABELS: Record<string, string> = {
  film: "Film",
  tv_series: "TV series",
  song: "Song",
};

function StarPicker({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex items-center gap-1" onMouseLeave={() => setHover(0)}>
      {[1, 2, 3, 4, 5].map((n) => {
        const filled = n <= (hover || value);
        return (
          <button
            key={n}
            type="button"
            onClick={() => onChange(n)}
            onMouseEnter={() => setHover(n)}
            className="p-0.5 transition-transform hover:scale-110"
          >
            <Star className={`h-7 w-7 ${filled ? "fill-amber-400 text-amber-400" : "text-zinc-300 dark:text-zinc-700"}`} />
          </button>
        );
      })}
    </div>
  );
}

function RatingDistribution({ reviews }: { reviews: TitleReview[] }) {
  const total = reviews.length;
  const counts = [5, 4, 3, 2, 1].map((star) => reviews.filter((r) => r.rating === star).length);
  return (
    <div className="flex flex-col gap-1.5">
      {[5, 4, 3, 2, 1].map((star, i) => {
        const count = counts[i];
        const pct = total > 0 ? (count / total) * 100 : 0;
        return (
          <div key={star} className="flex items-center gap-2 text-xs">
            <span className="flex w-8 items-center gap-0.5 font-semibold text-zinc-600 dark:text-zinc-400">
              {star} <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
            </span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
              <div className="h-full rounded-full bg-amber-400" style={{ width: `${pct}%` }} />
            </div>
            <span className="w-6 text-right text-zinc-500">{count}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function TitleDetailPage() {
  const params = useParams();
  const titleId = params.id as string;
  const { user, token } = useAuth();

  const [title, setTitle] = useState<Title | null>(null);
  const [reviews, setReviews] = useState<TitleReview[]>([]);
  const [myReview, setMyReview] = useState<TitleReview | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [rating, setRating] = useState(0);
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [t, r] = await Promise.all([api.getTitle(titleId), api.listTitleReviews(titleId)]);
      setTitle(t);
      setReviews(r);
      if (token) {
        const mine = await api.getMyTitleReview(titleId, token);
        setMyReview(mine);
        if (mine) {
          setRating(mine.rating);
          setBody(mine.body ?? "");
        }
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setNotFound(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [titleId, token]);

  const otherReviews = useMemo(() => reviews.filter((r) => !myReview || r.id !== myReview.id), [reviews, myReview]);

  async function handleSubmitReview(e: React.FormEvent) {
    e.preventDefault();
    if (!token || rating < 1) return;
    setSubmitting(true);
    setFormError(null);
    try {
      await api.submitTitleReview(titleId, { rating, body: body.trim() || undefined }, token);
      await load();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Could not submit your review.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteReview() {
    if (!token) return;
    setSubmitting(true);
    try {
      await api.deleteMyTitleReview(titleId, token);
      setRating(0);
      setBody("");
      await load();
    } finally {
      setSubmitting(false);
    }
  }

  if (notFound) {
    return (
      <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-14">
        <p className="text-zinc-500">This title couldn't be found.</p>
      </main>
    );
  }

  if (loading || !title) {
    return <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-14 text-zinc-500">Loading…</main>;
  }

  return (
    <main className="flex-1">
      <div className="relative overflow-hidden bg-zinc-950">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(244,63,94,0.2),transparent_60%)]" />
        <div className="relative mx-auto flex max-w-4xl flex-col gap-8 px-6 py-12 sm:flex-row">
          <div className="mx-auto w-40 shrink-0 overflow-hidden rounded-lg shadow-2xl sm:mx-0 sm:w-52">
            <TitlePoster name={title.name} workType={title.work_type} posterUrl={title.poster_url} className="aspect-[2/3] h-full w-full" iconClassName="h-14 w-14" />
          </div>
          <div className="flex-1">
            <span className="text-xs font-bold uppercase tracking-widest text-rose-400">{WORK_TYPE_LABELS[title.work_type]}</span>
            <div className="mt-1 flex flex-wrap items-start justify-between gap-3">
              <h1 className="font-heading text-3xl font-black text-white sm:text-4xl">{title.name}</h1>
              <ReportButton targetType="title" targetId={title.id} />
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-sm text-zinc-400">
              {title.release_year && <span>{title.release_year}</span>}
              {title.genre && <span>· {title.genre}</span>}
              {title.language && <span>· {title.language}</span>}
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-8">
              <div className="flex items-center gap-3">
                <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-lg bg-zinc-900 ring-1 ring-amber-400/30">
                  <Star className="h-8 w-8 fill-amber-400 text-amber-400" />
                </div>
                <div>
                  {title.average_rating != null ? (
                    <>
                      <p className="font-heading text-3xl font-black leading-none text-white">
                        {title.average_rating.toFixed(1)}
                        <span className="text-base font-medium text-zinc-500">/5</span>
                      </p>
                      <p className="text-xs text-zinc-500">
                        {title.review_count} rating{title.review_count === 1 ? "" : "s"}
                      </p>
                    </>
                  ) : (
                    <p className="text-sm text-zinc-500">Not yet rated</p>
                  )}
                </div>
              </div>
              {reviews.length > 0 && (
                <div className="w-full max-w-[14rem] sm:w-56">
                  <RatingDistribution reviews={reviews} />
                </div>
              )}
            </div>

            {title.synopsis && <p className="mt-6 max-w-xl text-sm leading-relaxed text-zinc-300">{title.synopsis}</p>}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-4xl px-6 py-10">
        <section className={sectionClass}>
          <h2 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">
            {myReview ? "Your rating" : "Rate this"}
          </h2>
          {user ? (
            <form onSubmit={handleSubmitReview} className="mt-3 flex flex-col gap-3">
              <StarPicker value={rating} onChange={setRating} />
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={3}
                placeholder="Write a critique (optional)"
                className={inputClass}
              />
              {formError && <p className="text-sm text-red-600">{formError}</p>}
              <div className="flex gap-2">
                <button type="submit" disabled={submitting || rating < 1} className={btnPrimary}>
                  {submitting ? "Saving…" : myReview ? "Update review" : "Submit review"}
                </button>
                {myReview && (
                  <button type="button" onClick={handleDeleteReview} disabled={submitting} className={btnSmall}>
                    Delete my review
                  </button>
                )}
              </div>
            </form>
          ) : (
            <p className="mt-3 text-sm text-zinc-500">
              <a href="/login" className="font-semibold text-rose-600 hover:underline">
                Log in
              </a>{" "}
              with a talent or recruiter account to rate and critique.
            </p>
          )}
        </section>

        <section className="mt-8">
          <h2 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">
            Critiques ({reviews.length})
          </h2>
          <div className="mt-4 flex flex-col gap-4">
            {reviews.length === 0 && <p className="text-sm text-zinc-500">No critiques yet.</p>}
            {myReview && <ReviewCard review={myReview} mine />}
            {otherReviews.map((r) => (
              <ReviewCard key={r.id} review={r} />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

function ReviewCard({ review, mine = false }: { review: TitleReview; mine?: boolean }) {
  return (
    <div className={`${sectionClass} flex gap-3`}>
      <AuthorAvatar name={review.author_name} />
      <div className="flex-1">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-zinc-900 dark:text-zinc-50">{review.author_name}</span>
            <span className="text-xs uppercase text-zinc-500">{review.author_role}</span>
            {mine && <span className="rounded-sm bg-rose-100 px-1.5 py-0.5 text-[10px] font-bold uppercase text-rose-700 dark:bg-rose-900/40 dark:text-rose-300">You</span>}
          </div>
          <div className="flex items-center gap-1">
            <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
            <span className="text-sm font-bold">{review.rating}</span>
          </div>
        </div>
        {review.body && <p className="mt-2 text-sm text-zinc-700 dark:text-zinc-300">{review.body}</p>}
        {!mine && (
          <div className="mt-2 flex justify-end">
            <ReportButton targetType="title_review" targetId={review.id} label="Report" />
          </div>
        )}
      </div>
    </div>
  );
}

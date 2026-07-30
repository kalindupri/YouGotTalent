"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Crown, ShieldCheck, Star } from "lucide-react";
import { ApiError, RecruiterProfile, RecruiterReviewSummary, api } from "@/lib/api";
import { neutralBadgeClass, premiumBadgeClass, recruiterTypeLabel, verifiedBadgeClass } from "@/lib/ui";

export default function RecruiterDetailPage() {
  const params = useParams<{ id: string }>();

  const [recruiter, setRecruiter] = useState<RecruiterProfile | null>(null);
  const [reviewSummary, setReviewSummary] = useState<RecruiterReviewSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getRecruiter(params.id)
      .then(setRecruiter)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this profile."));
    api.getRecruiterReviews(params.id).then(setReviewSummary).catch(() => {});
  }, [params.id]);

  if (error) {
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <p className="text-sm text-red-600">{error}</p>
      </main>
    );
  }

  if (!recruiter) {
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <p className="text-sm text-zinc-500">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
      <div className="flex items-center gap-4">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-sm bg-rose-600 text-xl font-black text-white">
          {recruiter.company_name.slice(0, 2).toUpperCase()}
        </div>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="font-heading text-3xl font-bold text-zinc-900 sm:text-4xl dark:text-zinc-50">
              {recruiter.company_name}
            </h1>
            <span className={neutralBadgeClass}>{recruiterTypeLabel(recruiter.recruiter_type)}</span>
            {recruiter.is_verified && (
              <span className={verifiedBadgeClass}>
                <ShieldCheck className="h-3 w-3" /> Verified
              </span>
            )}
            {recruiter.tier === "premium" && (
              <span className={premiumBadgeClass}>
                <Crown className="h-3 w-3" fill="currentColor" strokeWidth={0} /> Premium
              </span>
            )}
          </div>
          {recruiter.industry && <p className="mt-1 text-sm text-zinc-500">{recruiter.industry}</p>}
        </div>
      </div>

      {reviewSummary && reviewSummary.review_count > 0 ? (
        <div className="mt-10 pb-10">
          <h2 className="flex items-center gap-2 font-heading text-2xl font-bold text-zinc-900 dark:text-zinc-50">
            Reviews
            <span className="flex items-center gap-1 text-base font-semibold text-amber-500">
              <Star className="h-4 w-4" fill="currentColor" strokeWidth={0} /> {reviewSummary.average_rating}
              <span className="text-sm font-normal text-zinc-500">({reviewSummary.review_count})</span>
            </span>
          </h2>
          <ul className="mt-4 flex flex-col gap-3">
            {reviewSummary.reviews.map((r) => (
              <li key={r.id} className="rounded-2xl border-2 border-zinc-100 p-4 text-sm dark:border-zinc-800">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-50">{r.reviewer_name}</span>
                  <span className="flex items-center gap-0.5 text-amber-500">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <Star key={n} className="h-3.5 w-3.5" fill={n <= r.rating ? "currentColor" : "none"} />
                    ))}
                  </span>
                </div>
                {r.comment && <p className="mt-1 text-zinc-600 dark:text-zinc-400">&ldquo;{r.comment}&rdquo;</p>}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-10 pb-10 text-sm text-zinc-500">No reviews yet.</p>
      )}
    </main>
  );
}

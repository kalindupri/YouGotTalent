"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Plus, Star } from "lucide-react";
import { api, Title, WorkType } from "@/lib/api";
import { btnPrimary, inputClass } from "@/lib/ui";
import TitlePoster from "@/components/TitlePoster";

const WORK_TYPE_LABELS: Record<WorkType, string> = {
  film: "Film",
  tv_series: "TV series",
  song: "Song",
};

type SortKey = "top_rated" | "newest" | "most_reviewed";

const SORT_LABELS: Record<SortKey, string> = {
  top_rated: "Top rated",
  newest: "Newest",
  most_reviewed: "Most reviewed",
};

export default function TitlesPage() {
  return (
    <Suspense fallback={null}>
      <TitlesPageContent />
    </Suspense>
  );
}

function TitlesPageContent() {
  const searchParams = useSearchParams();
  const [titles, setTitles] = useState<Title[]>([]);
  const [workType, setWorkType] = useState<WorkType | "">((searchParams.get("work_type") as WorkType | null) ?? "");
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [sort, setSort] = useState<SortKey>("top_rated");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      async function load() {
        setLoading(true);
        setError(null);
        try {
          setTitles(await api.listTitles({ work_type: workType || undefined, q: q || undefined }));
        } catch {
          setError("Could not load titles right now.");
        } finally {
          setLoading(false);
        }
      }
      load();
    }, 250);
    return () => clearTimeout(handle);
  }, [workType, q]);

  const sortedTitles = useMemo(() => {
    const copy = [...titles];
    if (sort === "top_rated") {
      copy.sort((a, b) => (b.average_rating ?? -1) - (a.average_rating ?? -1));
    } else if (sort === "most_reviewed") {
      copy.sort((a, b) => b.review_count - a.review_count);
    } else {
      copy.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    }
    return copy;
  }, [titles, sort]);

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-14">
      <div className="relative overflow-hidden rounded-2xl bg-zinc-950 px-8 py-14 sm:px-14">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(244,63,94,0.25),transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:40px_40px]" />
        <div className="relative flex flex-wrap items-end justify-between gap-6">
          <div>
            <span className="inline-flex items-center gap-1 rounded-sm bg-amber-400 px-3 py-1 text-xs font-black uppercase tracking-widest text-zinc-900">
              <Star className="h-3 w-3 fill-current" /> Rate &amp; critique
            </span>
            <h1 className="mt-4 font-heading text-4xl font-black uppercase tracking-tight text-white sm:text-5xl">
              Sri Lanka's screen &amp; sound
            </h1>
            <p className="mt-3 max-w-lg text-zinc-400">
              Films, TV series, and songs — scored and critiqued by the talent and recruiters who make them.
            </p>
          </div>
          <Link href="/community/titles/new" className={`${btnPrimary} shrink-0`}>
            <Plus className="h-4 w-4" /> Add a title
          </Link>
        </div>
      </div>

      <div className="sticky top-16 z-10 mt-8 flex flex-wrap items-center gap-3 rounded-xl border border-zinc-200 bg-white/90 p-3 backdrop-blur dark:border-zinc-800 dark:bg-zinc-900/90">
        <div className="flex flex-wrap gap-1.5">
          <PillButton active={workType === ""} onClick={() => setWorkType("")}>
            All
          </PillButton>
          {(Object.keys(WORK_TYPE_LABELS) as WorkType[]).map((t) => (
            <PillButton key={t} active={workType === t} onClick={() => setWorkType(t)}>
              {WORK_TYPE_LABELS[t]}
            </PillButton>
          ))}
        </div>
        <input
          placeholder="Search by title, genre..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={`${inputClass} max-w-xs`}
        />
        <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} className={`${inputClass} ml-auto w-auto`}>
          {(Object.keys(SORT_LABELS) as SortKey[]).map((s) => (
            <option key={s} value={s}>
              {SORT_LABELS[s]}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="mt-8 text-sm text-red-600">{error}</p>}
      {!loading && !error && sortedTitles.length === 0 && (
        <p className="mt-8 text-sm text-zinc-500">No titles yet — be the first to add one.</p>
      )}

      <div className="mt-8 grid grid-cols-2 gap-x-5 gap-y-8 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {sortedTitles.map((t) => (
          <Link key={t.id} href={`/community/titles/${t.id}`} className="group flex flex-col gap-2">
            <div className="relative aspect-[2/3] overflow-hidden rounded-lg shadow-sm transition-all group-hover:-translate-y-1 group-hover:shadow-xl">
              <TitlePoster name={t.name} workType={t.work_type} posterUrl={t.poster_url} className="h-full w-full transition-transform duration-300 group-hover:scale-105" />
              {t.average_rating != null && (
                <span className="absolute left-1.5 top-1.5 flex items-center gap-0.5 rounded-sm bg-black/75 px-1.5 py-0.5 text-xs font-bold text-amber-400 backdrop-blur-sm">
                  <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                  {t.average_rating.toFixed(1)}
                </span>
              )}
              <span className="absolute right-1.5 top-1.5 rounded-sm bg-black/75 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white backdrop-blur-sm">
                {WORK_TYPE_LABELS[t.work_type]}
              </span>
            </div>
            <div>
              <p className="truncate font-heading text-sm font-bold text-zinc-900 dark:text-zinc-50">{t.name}</p>
              <p className="text-xs text-zinc-500">
                {t.release_year ?? ""}
                {t.release_year && t.genre ? " · " : ""}
                {t.genre ?? ""}
              </p>
            </div>
          </Link>
        ))}
        {loading &&
          Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-2">
              <div className="aspect-[2/3] animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-800" />
              <div className="h-3 w-3/4 animate-pulse rounded bg-zinc-100 dark:bg-zinc-800" />
            </div>
          ))}
      </div>
    </main>
  );
}

function PillButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3.5 py-1.5 text-xs font-bold uppercase tracking-wide transition-colors ${
        active
          ? "bg-rose-600 text-white"
          : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
      }`}
    >
      {children}
    </button>
  );
}

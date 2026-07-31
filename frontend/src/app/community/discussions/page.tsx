"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Flame, MessageCircle, Plus } from "lucide-react";
import { DiscussionCategory, DiscussionThread, api } from "@/lib/api";
import { btnPrimary, discussionCategoryMeta, formatRelativeTime, inputClass } from "@/lib/ui";
import AuthorAvatar from "@/components/AuthorAvatar";

const CATEGORIES: DiscussionCategory[] = ["films", "tv_series", "music", "industry_news", "general"];

export default function DiscussionsPage() {
  return (
    <Suspense fallback={null}>
      <DiscussionsPageContent />
    </Suspense>
  );
}

function DiscussionsPageContent() {
  const searchParams = useSearchParams();
  const [threads, setThreads] = useState<DiscussionThread[]>([]);
  const [category, setCategory] = useState<DiscussionCategory | "">(
    (searchParams.get("category") as DiscussionCategory | null) ?? ""
  );
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      async function load() {
        setLoading(true);
        setError(null);
        try {
          setThreads(await api.listDiscussions({ category: category || undefined, q: q || undefined }));
        } catch {
          setError("Could not load discussions right now.");
        } finally {
          setLoading(false);
        }
      }
      load();
    }, 250);
    return () => clearTimeout(handle);
  }, [category, q]);

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-14">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-4xl font-black uppercase tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
            Discussions
          </h1>
          <p className="mt-2 text-zinc-500">Talk films, songs, TV series, and the industry with talent and recruiters.</p>
        </div>
        <Link href="/community/discussions/new" className={btnPrimary}>
          <Plus className="h-4 w-4" /> Start a discussion
        </Link>
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-3">
        <div className="flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => setCategory("")}
            className={`rounded-full px-3.5 py-1.5 text-xs font-bold uppercase tracking-wide transition-colors ${
              category === "" ? "bg-rose-600 text-white" : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300"
            }`}
          >
            All
          </button>
          {CATEGORIES.map((c) => {
            const meta = discussionCategoryMeta(c);
            const Icon = meta.icon;
            const active = category === c;
            return (
              <button
                key={c}
                type="button"
                onClick={() => setCategory(c)}
                className={`inline-flex items-center gap-1 rounded-full px-3.5 py-1.5 text-xs font-bold uppercase tracking-wide transition-colors ${
                  active ? `${meta.solid} text-white` : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300"
                }`}
              >
                <Icon className="h-3.5 w-3.5" /> {meta.label}
              </button>
            );
          })}
        </div>
        <input
          placeholder="Search discussions..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={`${inputClass} ml-auto max-w-xs`}
        />
      </div>

      {error && <p className="mt-8 text-sm text-red-600">{error}</p>}
      {!loading && !error && threads.length === 0 && (
        <p className="mt-8 text-sm text-zinc-500">No discussions yet — start the first one.</p>
      )}

      <div className="mt-8 flex flex-col gap-3">
        {threads.map((t) => {
          const meta = discussionCategoryMeta(t.category);
          const Icon = meta.icon;
          const hot = t.reply_count >= 5;
          return (
            <Link
              key={t.id}
              href={`/community/discussions/${t.id}`}
              className={`flex gap-3 rounded-xl border border-zinc-200 border-l-4 bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 ${meta.border}`}
            >
              <AuthorAvatar name={t.author_name} className="mt-0.5 h-10 w-10 text-sm" />
              <div className="min-w-0 flex-1">
                <span className={`inline-flex items-center gap-1 rounded-sm px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${meta.soft}`}>
                  <Icon className="h-3 w-3" /> {meta.label}
                </span>
                <p className="mt-1 truncate font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">{t.subject}</p>
                <p className="mt-0.5 line-clamp-1 text-sm text-zinc-500">{t.body}</p>
                <div className="mt-2 flex items-center gap-3 text-xs text-zinc-500">
                  <span className="font-semibold text-zinc-700 dark:text-zinc-300">{t.author_name}</span>
                  <span>{formatRelativeTime(t.created_at)}</span>
                </div>
              </div>
              <div className="flex shrink-0 flex-col items-center justify-center gap-0.5 rounded-lg bg-zinc-50 px-3 py-2 dark:bg-zinc-800/60">
                {hot && <Flame className="h-3.5 w-3.5 fill-amber-500 text-amber-500" />}
                <span className="flex items-center gap-1 text-sm font-bold text-zinc-900 dark:text-zinc-50">
                  <MessageCircle className="h-3.5 w-3.5" /> {t.reply_count}
                </span>
              </div>
            </Link>
          );
        })}
        {loading &&
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900" />
          ))}
      </div>
    </main>
  );
}

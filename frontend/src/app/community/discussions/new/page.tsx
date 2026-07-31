"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ApiError, DiscussionCategory, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnPrimary, btnSecondary, discussionCategoryMeta, inputClass, labelClass, sectionClass } from "@/lib/ui";

const CATEGORIES: DiscussionCategory[] = ["films", "tv_series", "music", "industry_news", "general"];

export default function NewDiscussionPage() {
  return (
    <Suspense fallback={null}>
      <NewDiscussionPageContent />
    </Suspense>
  );
}

function NewDiscussionPageContent() {
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const titleId = searchParams.get("title_id") ?? undefined;

  const [category, setCategory] = useState<DiscussionCategory>("general");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?next=/community/discussions/new");
    }
  }, [authLoading, user, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token || !subject.trim() || !body.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const thread = await api.createDiscussion({ category, subject: subject.trim(), body: body.trim(), title_id: titleId }, token);
      router.push(`/community/discussions/${thread.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start this discussion right now.");
    } finally {
      setSubmitting(false);
    }
  }

  if (authLoading || !user) return null;

  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-14">
      <h1 className="font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
        Start a discussion
      </h1>

      <form onSubmit={handleSubmit} className={`${sectionClass} mt-8 flex flex-col gap-4`}>
        <label className={labelClass}>
          Category
          <div className="flex flex-wrap gap-1.5">
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
        </label>
        <label className={labelClass}>
          Subject
          <input value={subject} onChange={(e) => setSubject(e.target.value)} required className={inputClass} />
        </label>
        <label className={labelClass}>
          What's on your mind?
          <textarea value={body} onChange={(e) => setBody(e.target.value)} required rows={5} className={inputClass} />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-end gap-3">
          <Link href="/community/discussions" className={btnSecondary}>
            Cancel
          </Link>
          <button type="submit" disabled={submitting || !subject.trim() || !body.trim()} className={btnPrimary}>
            {submitting ? "Posting…" : "Post"}
          </button>
        </div>
      </form>
    </main>
  );
}

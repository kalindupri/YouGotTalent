"use client";

import { useEffect, useState } from "react";
import { Star, Trash2 } from "lucide-react";
import { DiscussionThread, Title, TitleReview, DiscussionReply, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnSmall, sectionClass } from "@/lib/ui";

const WORK_TYPE_LABELS: Record<string, string> = {
  film: "Film",
  tv_series: "TV series",
  song: "Song",
};

function TitlesModeration() {
  const { token } = useAuth();
  const [titles, setTitles] = useState<Title[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [reviews, setReviews] = useState<TitleReview[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);

  function refresh() {
    api.listTitles().then(setTitles).catch(() => {});
  }

  useEffect(refresh, []);

  async function toggleExpand(title: Title) {
    if (expandedId === title.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(title.id);
    setReviews(await api.listTitleReviews(title.id));
  }

  async function handleDeleteTitle(id: string) {
    if (!token) return;
    setBusyId(id);
    try {
      await api.adminDeleteTitle(id, token);
      setTitles((prev) => prev.filter((t) => t.id !== id));
      if (expandedId === id) setExpandedId(null);
    } finally {
      setBusyId(null);
    }
  }

  async function handleDeleteReview(reviewId: string, titleId: string) {
    if (!token) return;
    setBusyId(reviewId);
    try {
      await api.adminDeleteTitleReview(reviewId, token);
      setReviews((prev) => prev.filter((r) => r.id !== reviewId));
      setTitles((prev) => prev.map((t) => (t.id === titleId ? { ...t, review_count: t.review_count - 1 } : t)));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Titles &amp; critiques</h2>
      <ul className="mt-4 flex flex-col gap-2">
        {titles.map((t) => (
          <li key={t.id} className="rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-50">{t.name}</p>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <span className={badgeClass("neutral")}>{WORK_TYPE_LABELS[t.work_type]}</span>
                  {t.average_rating != null && (
                    <span className="flex items-center gap-1 text-xs text-zinc-500">
                      <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> {t.average_rating.toFixed(1)} ({t.review_count})
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => toggleExpand(t)} className={btnSmall}>
                  {expandedId === t.id ? "Hide reviews" : "View reviews"}
                </button>
                <button
                  disabled={busyId === t.id}
                  onClick={() => handleDeleteTitle(t.id)}
                  className={`${btnSmall} !border-red-300 !text-red-600 hover:!border-red-500`}
                >
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </button>
              </div>
            </div>

            {expandedId === t.id && (
              <div className="mt-3 flex flex-col gap-2 border-t border-zinc-200 pt-3 dark:border-zinc-800">
                {reviews.length === 0 && <p className="text-xs text-zinc-500">No reviews yet.</p>}
                {reviews.map((r) => (
                  <div key={r.id} className="flex items-center justify-between gap-3 text-xs text-zinc-600 dark:text-zinc-400">
                    <div className="min-w-0 flex-1">
                      <span className="font-semibold text-zinc-800 dark:text-zinc-200">{r.author_name}</span>{" "}
                      <span className="uppercase">{r.author_role}</span> · {r.rating}★
                      {r.body && <p className="mt-0.5 truncate">{r.body}</p>}
                    </div>
                    <button
                      disabled={busyId === r.id}
                      onClick={() => handleDeleteReview(r.id, t.id)}
                      className="shrink-0 text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </li>
        ))}
        {titles.length === 0 && <p className="text-sm text-zinc-500">No titles yet.</p>}
      </ul>
    </section>
  );
}

function DiscussionsModeration() {
  const { token } = useAuth();
  const [threads, setThreads] = useState<DiscussionThread[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [replies, setReplies] = useState<DiscussionReply[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);

  function refresh() {
    api.listDiscussions().then(setThreads).catch(() => {});
  }

  useEffect(refresh, []);

  async function toggleExpand(thread: DiscussionThread) {
    if (expandedId === thread.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(thread.id);
    setReplies(await api.listDiscussionReplies(thread.id));
  }

  async function handleDeleteThread(id: string) {
    if (!token) return;
    setBusyId(id);
    try {
      await api.adminDeleteThread(id, token);
      setThreads((prev) => prev.filter((t) => t.id !== id));
      if (expandedId === id) setExpandedId(null);
    } finally {
      setBusyId(null);
    }
  }

  async function handleDeleteReply(replyId: string, threadId: string) {
    if (!token) return;
    setBusyId(replyId);
    try {
      await api.adminDeleteReply(replyId, token);
      setReplies((prev) => prev.filter((r) => r.id !== replyId));
      setThreads((prev) => prev.map((t) => (t.id === threadId ? { ...t, reply_count: t.reply_count - 1 } : t)));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Discussions</h2>
      <ul className="mt-4 flex flex-col gap-2">
        {threads.map((t) => (
          <li key={t.id} className="rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-50">{t.subject}</p>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <span className={badgeClass("neutral")}>{t.category.replace("_", " ")}</span>
                  <span className="text-xs text-zinc-500">
                    {t.author_name} · {t.reply_count} repl{t.reply_count === 1 ? "y" : "ies"}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => toggleExpand(t)} className={btnSmall}>
                  {expandedId === t.id ? "Hide replies" : "View replies"}
                </button>
                <button
                  disabled={busyId === t.id}
                  onClick={() => handleDeleteThread(t.id)}
                  className={`${btnSmall} !border-red-300 !text-red-600 hover:!border-red-500`}
                >
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </button>
              </div>
            </div>

            {expandedId === t.id && (
              <div className="mt-3 flex flex-col gap-2 border-t border-zinc-200 pt-3 dark:border-zinc-800">
                {replies.length === 0 && <p className="text-xs text-zinc-500">No replies yet.</p>}
                {replies.map((r) => (
                  <div key={r.id} className="flex items-center justify-between gap-3 text-xs text-zinc-600 dark:text-zinc-400">
                    <div className="min-w-0 flex-1">
                      <span className="font-semibold text-zinc-800 dark:text-zinc-200">{r.author_name}</span>{" "}
                      <span className="uppercase">{r.author_role}</span>
                      <p className="mt-0.5 truncate">{r.body}</p>
                    </div>
                    <button
                      disabled={busyId === r.id}
                      onClick={() => handleDeleteReply(r.id, t.id)}
                      className="shrink-0 text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </li>
        ))}
        {threads.length === 0 && <p className="text-sm text-zinc-500">No discussions yet.</p>}
      </ul>
    </section>
  );
}

export default function CommunityModeration() {
  return (
    <div className="flex flex-col gap-6">
      <TitlesModeration />
      <DiscussionsModeration />
    </div>
  );
}

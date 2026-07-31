"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ApiError, DiscussionReply, DiscussionThread, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnPrimary, discussionCategoryMeta, formatRelativeTime, inputClass, sectionClass } from "@/lib/ui";
import ReportButton from "@/components/ReportButton";
import AuthorAvatar from "@/components/AuthorAvatar";

export default function DiscussionDetailPage() {
  const params = useParams();
  const threadId = params.id as string;
  const { user, token } = useAuth();

  const [thread, setThread] = useState<DiscussionThread | null>(null);
  const [replies, setReplies] = useState<DiscussionReply[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [replyBody, setReplyBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [t, r] = await Promise.all([api.getDiscussion(threadId), api.listDiscussionReplies(threadId)]);
      setThread(t);
      setReplies(r);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setNotFound(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId]);

  async function handleReply(e: FormEvent) {
    e.preventDefault();
    if (!token || !replyBody.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.createDiscussionReply(threadId, { body: replyBody.trim() }, token);
      setReplyBody("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not post your reply.");
    } finally {
      setSubmitting(false);
    }
  }

  if (notFound) {
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
        <p className="text-zinc-500">This discussion couldn't be found.</p>
      </main>
    );
  }

  if (loading || !thread) {
    return <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14 text-zinc-500">Loading…</main>;
  }

  const meta = discussionCategoryMeta(thread.category);
  const Icon = meta.icon;

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
      <span className={`inline-flex items-center gap-1 rounded-sm px-2.5 py-1 text-xs font-bold uppercase tracking-wide ${meta.soft}`}>
        <Icon className="h-3.5 w-3.5" /> {meta.label}
      </span>
      <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
        <h1 className="font-heading text-3xl font-black text-zinc-900 sm:text-4xl dark:text-zinc-50">{thread.subject}</h1>
        <ReportButton targetType="discussion_thread" targetId={thread.id} />
      </div>
      <div className="mt-3 flex items-center gap-3">
        <AuthorAvatar name={thread.author_name} />
        <div className="text-sm">
          <p className="font-semibold text-zinc-900 dark:text-zinc-50">{thread.author_name}</p>
          <p className="text-xs uppercase text-zinc-500">
            {thread.author_role} · {formatRelativeTime(thread.created_at)}
          </p>
        </div>
      </div>
      {thread.title_id && (
        <Link href={`/community/titles/${thread.title_id}`} className="mt-3 inline-block text-sm font-semibold text-rose-600 hover:underline">
          View linked title →
        </Link>
      )}
      <p className="mt-4 whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">{thread.body}</p>

      <section className="mt-10">
        <h2 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">
          Replies ({replies.length})
        </h2>
        <div className="mt-4 flex flex-col gap-4">
          {replies.length === 0 && <p className="text-sm text-zinc-500">No replies yet.</p>}
          {replies.map((r) => (
            <div key={r.id} className={`${sectionClass} flex gap-3`}>
              <AuthorAvatar name={r.author_name} />
              <div className="flex-1">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-50">{r.author_name}</span>
                  <span className="text-xs uppercase text-zinc-500">{r.author_role}</span>
                  <span className="text-xs text-zinc-500">{formatRelativeTime(r.created_at)}</span>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-700 dark:text-zinc-300">{r.body}</p>
                <div className="mt-2 flex justify-end">
                  <ReportButton targetType="discussion_reply" targetId={r.id} label="Report" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={`${sectionClass} mt-8`}>
        {user ? (
          <form onSubmit={handleReply} className="flex gap-3">
            <AuthorAvatar name={user.full_name ?? "You"} className="mt-0.5 h-9 w-9 text-xs" />
            <div className="flex flex-1 flex-col gap-3">
              <textarea
                value={replyBody}
                onChange={(e) => setReplyBody(e.target.value)}
                rows={3}
                placeholder="Add to the discussion..."
                className={inputClass}
              />
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div className="flex justify-end">
                <button type="submit" disabled={submitting || !replyBody.trim()} className={btnPrimary}>
                  {submitting ? "Posting…" : "Reply"}
                </button>
              </div>
            </div>
          </form>
        ) : (
          <p className="text-sm text-zinc-500">
            <a href="/login" className="font-semibold text-rose-600 hover:underline">
              Log in
            </a>{" "}
            with a talent or recruiter account to reply.
          </p>
        )}
      </section>
    </main>
  );
}

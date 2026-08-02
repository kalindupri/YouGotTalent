"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ApiError, DiscussionReply, DiscussionThread, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnPrimary, btnSmall, discussionCategoryMeta, formatRelativeTime, inputClass, sectionClass } from "@/lib/ui";
import ReportButton from "@/components/ReportButton";
import AuthorAvatar from "@/components/AuthorAvatar";

export default function DiscussionDetailPage() {
  const params = useParams();
  const threadId = params.id as string;
  const router = useRouter();
  const { user, token } = useAuth();

  const [thread, setThread] = useState<DiscussionThread | null>(null);
  const [replies, setReplies] = useState<DiscussionReply[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [replyBody, setReplyBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [editingThread, setEditingThread] = useState(false);
  const [editSubject, setEditSubject] = useState("");
  const [editBody, setEditBody] = useState("");
  const [threadActionError, setThreadActionError] = useState<string | null>(null);
  const [threadActionBusy, setThreadActionBusy] = useState(false);

  const [editingReplyId, setEditingReplyId] = useState<string | null>(null);
  const [editReplyBody, setEditReplyBody] = useState("");
  const [replyActionBusy, setReplyActionBusy] = useState<string | null>(null);

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

  function startEditThread() {
    if (!thread) return;
    setEditSubject(thread.subject);
    setEditBody(thread.body);
    setThreadActionError(null);
    setEditingThread(true);
  }

  async function handleSaveThread(e: FormEvent) {
    e.preventDefault();
    if (!token || !thread) return;
    setThreadActionBusy(true);
    setThreadActionError(null);
    try {
      const updated = await api.updateDiscussion(thread.id, { subject: editSubject, body: editBody }, token);
      setThread(updated);
      setEditingThread(false);
    } catch (err) {
      setThreadActionError(err instanceof ApiError ? err.message : "Could not save these changes.");
    } finally {
      setThreadActionBusy(false);
    }
  }

  async function handleDeleteThread() {
    if (!token || !thread) return;
    if (!window.confirm("Delete this discussion? All its replies will be removed too.")) return;
    setThreadActionBusy(true);
    try {
      await api.deleteDiscussion(thread.id, token);
      router.push("/community/discussions");
    } catch {
      setThreadActionError("Could not delete this discussion.");
      setThreadActionBusy(false);
    }
  }

  function startEditReply(reply: DiscussionReply) {
    setEditingReplyId(reply.id);
    setEditReplyBody(reply.body);
  }

  async function handleSaveReply(e: FormEvent, replyId: string) {
    e.preventDefault();
    if (!token) return;
    setReplyActionBusy(replyId);
    try {
      const updated = await api.updateDiscussionReply(threadId, replyId, { body: editReplyBody }, token);
      setReplies((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      setEditingReplyId(null);
    } catch {
      setError("Could not save this reply.");
    } finally {
      setReplyActionBusy(null);
    }
  }

  async function handleDeleteReply(replyId: string) {
    if (!token) return;
    if (!window.confirm("Delete this reply?")) return;
    setReplyActionBusy(replyId);
    try {
      await api.deleteDiscussionReply(threadId, replyId, token);
      setReplies((prev) => prev.filter((r) => r.id !== replyId));
    } catch {
      setError("Could not delete this reply.");
    } finally {
      setReplyActionBusy(null);
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
        <div className="flex items-center gap-3">
          {user && user.id === thread.author_user_id && (
            <>
              <button
                type="button"
                onClick={() => (editingThread ? setEditingThread(false) : startEditThread())}
                className="text-sm font-semibold text-zinc-600 hover:underline dark:text-zinc-300"
              >
                {editingThread ? "Cancel" : "Edit"}
              </button>
              <button
                type="button"
                disabled={threadActionBusy}
                onClick={handleDeleteThread}
                className="text-sm font-semibold text-red-600 hover:underline disabled:opacity-50"
              >
                Delete
              </button>
            </>
          )}
          <ReportButton targetType="discussion_thread" targetId={thread.id} />
        </div>
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

      {editingThread ? (
        <form onSubmit={handleSaveThread} className={`${sectionClass} mt-4 flex flex-col gap-3`}>
          <input value={editSubject} onChange={(e) => setEditSubject(e.target.value)} className={inputClass} />
          <textarea rows={4} value={editBody} onChange={(e) => setEditBody(e.target.value)} className={inputClass} />
          {threadActionError && <p className="text-sm text-red-600">{threadActionError}</p>}
          <button type="submit" disabled={threadActionBusy} className={`w-fit ${btnPrimary}`}>
            {threadActionBusy ? "Saving…" : "Save changes"}
          </button>
        </form>
      ) : (
        <p className="mt-4 whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">{thread.body}</p>
      )}
      {threadActionError && !editingThread && <p className="mt-2 text-sm text-red-600">{threadActionError}</p>}

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
                {editingReplyId === r.id ? (
                  <form onSubmit={(e) => handleSaveReply(e, r.id)} className="mt-2 flex flex-col gap-2">
                    <textarea
                      rows={3}
                      value={editReplyBody}
                      onChange={(e) => setEditReplyBody(e.target.value)}
                      className={inputClass}
                    />
                    <div className="flex items-center gap-2">
                      <button type="submit" disabled={replyActionBusy === r.id} className={btnSmall}>
                        Save
                      </button>
                      <button type="button" onClick={() => setEditingReplyId(null)} className={btnSmall}>
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-700 dark:text-zinc-300">{r.body}</p>
                )}
                <div className="mt-2 flex items-center justify-end gap-3">
                  {user && user.id === r.author_user_id && editingReplyId !== r.id && (
                    <>
                      <button
                        type="button"
                        onClick={() => startEditReply(r)}
                        className="text-xs font-semibold text-zinc-500 hover:underline dark:text-zinc-400"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        disabled={replyActionBusy === r.id}
                        onClick={() => handleDeleteReply(r.id)}
                        className="text-xs font-semibold text-red-600 hover:underline disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </>
                  )}
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

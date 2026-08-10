"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Check, CheckCheck } from "lucide-react";
import { ConversationSummary, Message, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnPrimary, formatTimestamp, inputClass } from "@/lib/ui";

const POLL_INTERVAL_MS = 4000;

export default function ConversationThreadPage() {
  const params = useParams<{ id: string }>();
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();

  const [conversation, setConversation] = useState<ConversationSummary | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [authLoading, user, router]);

  useEffect(() => {
    if (!token) return;
    api.listConversations(token).then((all) => {
      setConversation(all.find((c) => c.id === params.id) ?? null);
    });
  }, [token, params.id]);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    async function load() {
      try {
        const list = await api.listMessages(params.id, token!);
        if (!cancelled) setMessages(list);
      } catch {
        if (!cancelled) setError("Could not load this conversation.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token, params.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    if (!token || !draft.trim()) return;
    setSending(true);
    setError(null);
    try {
      const message = await api.sendMessage(params.id, draft.trim(), token);
      setMessages((prev) => [...prev, message]);
      setDraft("");
    } catch {
      setError("Could not send that message.");
    } finally {
      setSending(false);
    }
  }

  if (authLoading || !user) {
    return (
      <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-14">
        <p className="text-sm text-zinc-500">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-6 py-10">
      <Link href="/messages" className="text-sm font-semibold text-rose-600 hover:underline">
        ← All messages
      </Link>
      <h1 className="mt-2 font-heading text-2xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
        {conversation?.other_party_name ?? "Conversation"}
      </h1>

      <div className="mt-6 flex flex-1 flex-col gap-3 overflow-y-auto rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-950" style={{ minHeight: "24rem" }}>
        {loading ? (
          <p className="text-sm text-zinc-500">Loading…</p>
        ) : messages.length === 0 ? (
          <p className="text-sm text-zinc-500">No messages yet — say hello.</p>
        ) : (
          messages.map((m) => {
            const mine = m.sender_user_id === user.id;
            return (
              <div key={m.id} className={`flex flex-col ${mine ? "items-end" : "items-start"}`}>
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                    mine
                      ? "bg-rose-600 text-white"
                      : "border-2 border-zinc-200 bg-white text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
                  }`}
                >
                  {m.body}
                </div>
                <div className="mt-1 flex items-center gap-1 text-xs text-zinc-400">
                  <span>{formatTimestamp(m.created_at)}</span>
                  {mine &&
                    (m.read_at ? (
                      <CheckCheck className="h-3.5 w-3.5 text-rose-500" aria-label="Seen" />
                    ) : (
                      <Check className="h-3.5 w-3.5" aria-label="Sent" />
                    ))}
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSend} className="mt-4 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Type a message…"
          className={inputClass}
        />
        <button type="submit" disabled={sending || !draft.trim()} className={btnPrimary}>
          Send
        </button>
      </form>
    </main>
  );
}

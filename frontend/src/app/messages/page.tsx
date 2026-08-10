"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ConversationSummary, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { eyebrowClass, formatTimestamp, sectionClass } from "@/lib/ui";

export default function MessagesInboxPage() {
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [authLoading, user, router]);

  useEffect(() => {
    if (!token) return;
    api
      .listConversations(token)
      .then(setConversations)
      .finally(() => setLoading(false));
  }, [token]);

  if (authLoading || !user) {
    return (
      <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-14">
        <p className="text-sm text-zinc-500">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-14">
      <span className={eyebrowClass}>Inbox</span>
      <h1 className="mt-2 font-heading text-4xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
        Messages
      </h1>

      {loading ? (
        <p className="mt-8 text-sm text-zinc-500">Loading…</p>
      ) : conversations.length === 0 ? (
        <div className={`${sectionClass} mt-8`}>
          <p className="text-sm text-zinc-500">
            {user.role === "recruiter"
              ? "No conversations yet — message a talent from their profile to get started."
              : "No conversations yet — organizers will reach out here when they want to talk about a role."}
          </p>
        </div>
      ) : (
        <ul className="mt-8 flex flex-col gap-3">
          {conversations
            .slice()
            .sort((a, b) => new Date(b.last_message_at ?? b.created_at).getTime() - new Date(a.last_message_at ?? a.created_at).getTime())
            .map((c) => (
              <li key={c.id}>
                <Link
                  href={`/messages/${c.id}`}
                  className={`${sectionClass} flex items-center justify-between gap-4 !p-4 transition-all hover:-translate-y-0.5 hover:border-rose-300 dark:hover:border-rose-800`}
                >
                  <div className="min-w-0">
                    <p className="font-semibold text-zinc-900 dark:text-zinc-50">{c.other_party_name}</p>
                    <p className="mt-0.5 truncate text-sm text-zinc-500">{c.last_message ?? "No messages yet"}</p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    {c.last_message_at && (
                      <span className="text-xs text-zinc-400">{formatTimestamp(c.last_message_at)}</span>
                    )}
                    {c.unread_count > 0 && (
                      <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-600 px-1.5 text-xs font-bold text-white">
                        {c.unread_count}
                      </span>
                    )}
                  </div>
                </Link>
              </li>
            ))}
        </ul>
      )}
    </main>
  );
}

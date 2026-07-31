"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { btnSmall } from "@/lib/ui";

const UNREAD_POLL_INTERVAL_MS = 30_000;

export default function Header() {
  const { user, token, loading, logout } = useAuth();
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!token || user?.role === "admin") {
      setUnreadCount(0);
      return;
    }
    let cancelled = false;
    function refresh() {
      api
        .listConversations(token!)
        .then((conversations) => {
          if (!cancelled) setUnreadCount(conversations.reduce((sum, c) => sum + c.unread_count, 0));
        })
        .catch(() => {});
    }
    refresh();
    const interval = setInterval(refresh, UNREAD_POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token, user]);

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-rose-600 text-sm font-black text-white">
            YT
          </span>
          <span className="font-heading text-lg font-black uppercase tracking-tight text-white">
            YouGotTalent
          </span>
        </Link>
        <nav className="flex items-center gap-6 text-sm font-semibold">
          <Link href="/talents" className="hidden text-zinc-300 hover:text-rose-500 sm:inline">
            Browse talent
          </Link>
          <Link href="/casting-calls" className="hidden text-zinc-300 hover:text-rose-500 sm:inline">
            Talent hunts
          </Link>
          <Link href="/community" className="hidden text-zinc-300 hover:text-rose-500 sm:inline">
            Community
          </Link>
          <Link href="/pricing" className="hidden text-zinc-300 hover:text-rose-500 sm:inline">
            Pricing
          </Link>
          {loading ? null : user ? (
            <>
              {user.role === "admin" ? (
                <Link href="/admin" className="text-zinc-300 hover:text-rose-500">
                  Admin
                </Link>
              ) : (
                <>
                  <Link href="/messages" className="relative text-zinc-300 hover:text-rose-500">
                    Messages
                    {unreadCount > 0 && (
                      <span className="absolute -right-3 -top-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-bold text-white">
                        {unreadCount > 9 ? "9+" : unreadCount}
                      </span>
                    )}
                  </Link>
                  <Link href="/dashboard" className="text-zinc-300 hover:text-rose-500">
                    Dashboard
                  </Link>
                </>
              )}
              <button onClick={handleLogout} className={`${btnSmall} !border-zinc-700 !text-zinc-300`}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-zinc-300 hover:text-rose-500">
                Log in
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center justify-center rounded-md bg-rose-600 px-5 py-2.5 text-sm font-bold uppercase tracking-wide text-white transition-colors hover:bg-rose-700"
              >
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

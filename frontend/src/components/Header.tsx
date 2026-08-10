"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { btnSmall } from "@/lib/ui";
import NotificationBell from "@/components/NotificationBell";

const UNREAD_POLL_INTERVAL_MS = 30_000;

export default function Header() {
  const { user, token, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [unreadCount, setUnreadCount] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);

  // Close the mobile menu on navigation rather than leaving it open over the new page.
  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

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

  const browseLinks = (
    <>
      <Link href="/talents" className="text-zinc-300 hover:text-rose-500">
        Browse talent
      </Link>
      <Link href="/casting-calls" className="text-zinc-300 hover:text-rose-500">
        Talent hunts
      </Link>
      <Link href="/community" className="text-zinc-300 hover:text-rose-500">
        Community
      </Link>
      <Link href="/pricing" className="text-zinc-300 hover:text-rose-500">
        Pricing
      </Link>
    </>
  );

  const accountLinks = loading ? null : user ? (
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
          {token && <NotificationBell token={token} />}
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
  );

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

        <nav className="hidden items-center gap-6 text-sm font-semibold sm:flex">
          {browseLinks}
          {accountLinks}
        </nav>

        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          className="flex h-10 w-10 items-center justify-center rounded-md text-zinc-300 hover:bg-zinc-900 hover:text-rose-500 sm:hidden"
        >
          {menuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {menuOpen && (
        <nav className="flex flex-col gap-1 border-t border-zinc-800 bg-zinc-950 px-6 py-4 text-base font-semibold [&>a]:py-2.5 [&>button]:py-2.5 sm:hidden">
          {browseLinks}
          <div className="my-2 border-t border-zinc-800" />
          {accountLinks}
        </nav>
      )}
    </header>
  );
}

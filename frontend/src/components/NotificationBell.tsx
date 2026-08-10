"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Bell } from "lucide-react";
import { Notification, api } from "@/lib/api";
import { formatTimestamp } from "@/lib/ui";

const POLL_INTERVAL_MS = 30_000;

export default function NotificationBell({ token }: { token: string }) {
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    function refreshCount() {
      api
        .unreadNotificationCount(token)
        .then((r) => {
          if (!cancelled) setUnreadCount(r.count);
        })
        .catch(() => {});
    }
    refreshCount();
    const interval = setInterval(refreshCount, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleOpen() {
    const next = !open;
    setOpen(next);
    if (next) {
      const list = await api.listNotifications(token).catch(() => []);
      setNotifications(list);
    }
  }

  async function handleSelect(n: Notification) {
    setOpen(false);
    if (!n.read_at) {
      api.markNotificationRead(n.id, token).catch(() => {});
      setUnreadCount((c) => Math.max(0, c - 1));
    }
    if (n.link_url) router.push(n.link_url);
  }

  async function handleMarkAllRead() {
    await api.markAllNotificationsRead(token).catch(() => {});
    setUnreadCount(0);
    setNotifications((prev) => prev.map((n) => ({ ...n, read_at: n.read_at ?? new Date().toISOString() })));
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={handleOpen}
        aria-label="Notifications"
        className="relative flex h-9 w-9 items-center justify-center rounded-md text-zinc-300 hover:bg-zinc-900 hover:text-rose-500"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-bold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-11 z-50 w-80 max-w-[90vw] rounded-xl border border-zinc-200 bg-white shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-2.5 dark:border-zinc-800">
            <span className="text-sm font-bold text-zinc-900 dark:text-zinc-50">Notifications</span>
            {unreadCount > 0 && (
              <button type="button" onClick={handleMarkAllRead} className="text-xs font-semibold text-rose-600 hover:underline">
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-zinc-500">No notifications yet.</p>
            ) : (
              notifications.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => handleSelect(n)}
                  className={`flex w-full flex-col items-start gap-0.5 border-b border-zinc-100 px-4 py-3 text-left text-sm last:border-0 hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800 ${
                    n.read_at ? "" : "bg-rose-50/50 dark:bg-rose-950/20"
                  }`}
                >
                  <span className="font-semibold text-zinc-900 dark:text-zinc-50">{n.title}</span>
                  {n.body && <span className="text-xs text-zinc-500">{n.body}</span>}
                  <span className="text-[11px] text-zinc-400">{formatTimestamp(n.created_at)}</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

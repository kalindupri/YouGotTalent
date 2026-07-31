"use client";

import { useEffect, useState } from "react";
import { AdminStats, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { sectionClass } from "@/lib/ui";

export default function StatsOverview() {
  const { token } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    if (!token) return;
    api.adminGetStats(token).then(setStats).catch(() => {});
  }, [token]);

  const tiles: { label: string; value: number | string }[] = stats
    ? [
        { label: "Total users", value: stats.total_users },
        { label: "Talents", value: stats.total_talents },
        { label: "Recruiters", value: stats.total_recruiters },
        { label: "Verified talents", value: stats.verified_talents },
        { label: "Verified recruiters", value: stats.verified_recruiters },
        { label: "Open talent hunts", value: stats.open_casting_calls },
        { label: "Closed talent hunts", value: stats.closed_casting_calls },
        { label: "Applications", value: stats.total_applications },
        { label: "Invitations", value: stats.total_invitations },
      ]
    : [];

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Platform overview</h2>
      {!stats ? (
        <p className="mt-2 text-sm text-zinc-500">Loading…</p>
      ) : (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {tiles.map((t) => (
            <div key={t.label} className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
              <p className="font-heading text-2xl font-black text-rose-600">{t.value}</p>
              <p className="mt-1 text-xs text-zinc-500">{t.label}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

"use client";

import StatsOverview from "@/components/admin/StatsOverview";

export default function AdminOverviewPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Overview</h1>
      <p className="mt-1 text-sm text-zinc-500">Platform-wide stats at a glance.</p>
      <div className="mt-6">
        <StatsOverview />
      </div>
    </div>
  );
}

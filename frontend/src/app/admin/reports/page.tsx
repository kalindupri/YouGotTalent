"use client";

import ReportQueue from "@/components/admin/ReportQueue";

export default function AdminReportsPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Reports</h1>
      <p className="mt-1 text-sm text-zinc-500">User-submitted reports on profiles, talent hunts, and community content.</p>
      <div className="mt-6">
        <ReportQueue />
      </div>
    </div>
  );
}

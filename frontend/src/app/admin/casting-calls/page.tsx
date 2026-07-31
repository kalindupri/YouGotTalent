"use client";

import CastingCallModeration from "@/components/admin/CastingCallModeration";

export default function AdminCastingCallsPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Talent hunts</h1>
      <p className="mt-1 text-sm text-zinc-500">Review and moderate posted talent hunts.</p>
      <div className="mt-6">
        <CastingCallModeration />
      </div>
    </div>
  );
}

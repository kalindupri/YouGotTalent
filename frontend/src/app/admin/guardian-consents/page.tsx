"use client";

import GuardianConsentQueue from "@/components/admin/GuardianConsentQueue";

export default function AdminGuardianConsentsPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Guardian consent</h1>
      <p className="mt-1 text-sm text-zinc-500">
        Review proof of guardianship for under-18 talent. Their profiles stay hidden until you approve.
      </p>
      <div className="mt-6">
        <GuardianConsentQueue />
      </div>
    </div>
  );
}

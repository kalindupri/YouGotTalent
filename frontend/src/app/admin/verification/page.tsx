"use client";

import VerificationQueue from "@/components/admin/VerificationQueue";

export default function AdminVerificationPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Verification</h1>
      <p className="mt-1 text-sm text-zinc-500">Approve or reject pending talent and recruiter verification requests.</p>
      <div className="mt-6">
        <VerificationQueue />
      </div>
    </div>
  );
}

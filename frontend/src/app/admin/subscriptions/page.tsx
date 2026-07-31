"use client";

import SubscriptionsPanel from "@/components/admin/SubscriptionsPanel";

export default function AdminSubscriptionsPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Subscriptions</h1>
      <p className="mt-1 text-sm text-zinc-500">View subscriptions, payment history, and run the dunning sweep.</p>
      <div className="mt-6">
        <SubscriptionsPanel />
      </div>
    </div>
  );
}

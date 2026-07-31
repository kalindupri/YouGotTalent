"use client";

import PricingManager from "@/components/admin/PricingManager";

export default function AdminPricingPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Pricing</h1>
      <p className="mt-1 text-sm text-zinc-500">Set current subscription prices and review the change history.</p>
      <div className="mt-6">
        <PricingManager />
      </div>
    </div>
  );
}

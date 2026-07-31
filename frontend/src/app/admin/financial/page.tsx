"use client";

import ChurnReasonsPanel from "@/components/admin/ChurnReasonsPanel";
import FinancialOverviewCard from "@/components/admin/FinancialOverviewCard";

export default function AdminFinancialPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Financial</h1>
      <p className="mt-1 text-sm text-zinc-500">Revenue, pricing scenarios, and churn reasons.</p>
      <div className="mt-6 flex flex-col gap-6">
        <FinancialOverviewCard />
        <ChurnReasonsPanel />
      </div>
    </div>
  );
}

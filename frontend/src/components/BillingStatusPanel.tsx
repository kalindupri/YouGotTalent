"use client";

import { useEffect, useState } from "react";
import { Subscription, api } from "@/lib/api";
import { btnSmall } from "@/lib/ui";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export default function BillingStatusPanel({ token, onCanceled }: { token: string; onCanceled?: () => void }) {
  const [sub, setSub] = useState<Subscription | null | undefined>(undefined);
  const [canceling, setCanceling] = useState(false);

  useEffect(() => {
    api
      .getMyBilling(token)
      .then(setSub)
      .catch(() => setSub(null));
  }, [token]);

  async function handleCancel() {
    setCanceling(true);
    try {
      const updated = await api.cancelMySubscription(token);
      setSub(updated);
      onCanceled?.();
    } finally {
      setCanceling(false);
    }
  }

  if (!sub) return null;

  const cyclePrice = `LKR ${sub.price_lkr.toLocaleString()}/${sub.billing_cycle === "annual" ? "yr" : "mo"}`;

  return (
    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs dark:border-zinc-800 dark:bg-zinc-900/60">
      <p className="text-zinc-600 dark:text-zinc-400">
        {sub.status === "trialing" && sub.trial_end && <>Free trial — ends {formatDate(sub.trial_end)}</>}
        {sub.status === "active" && sub.current_period_end && (
          <>
            Renews {formatDate(sub.current_period_end)} · {cyclePrice}
          </>
        )}
        {sub.status === "past_due" && <>Payment issue on your last renewal — please update your billing details.</>}
        {sub.status === "canceled" && <>Subscription canceled{sub.canceled_at ? ` on ${formatDate(sub.canceled_at)}` : ""}.</>}
        {sub.status === "expired" && <>Your trial or billing period has ended.</>}
        {sub.status === "pending" && <>Checkout in progress…</>}
      </p>
      {(sub.status === "trialing" || sub.status === "active" || sub.status === "past_due") && (
        <button onClick={handleCancel} disabled={canceling} className={btnSmall}>
          {canceling ? "Canceling…" : "Cancel subscription"}
        </button>
      )}
    </div>
  );
}

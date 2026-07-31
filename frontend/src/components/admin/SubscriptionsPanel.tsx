"use client";

import { useEffect, useState } from "react";
import { AdminSubscription, Payment, SubscriptionStatusCode, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnSmall, inputClass, sectionClass } from "@/lib/ui";

const SUBSCRIPTION_STATUS_TONE: Record<SubscriptionStatusCode, "success" | "warning" | "neutral" | "info"> = {
  trialing: "info",
  pending: "neutral",
  active: "success",
  past_due: "warning",
  canceled: "neutral",
  expired: "neutral",
};

export default function SubscriptionsPanel() {
  const { token } = useAuth();
  const [subs, setSubs] = useState<AdminSubscription[]>([]);
  const [statusFilter, setStatusFilter] = useState<SubscriptionStatusCode | "">("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [sweeping, setSweeping] = useState(false);
  const [sweepResult, setSweepResult] = useState<string | null>(null);

  function refresh() {
    if (!token) return;
    api.adminListSubscriptions({ status: statusFilter || undefined }, token).then(setSubs).catch(() => {});
  }

  useEffect(refresh, [statusFilter, token]);

  async function toggleExpand(sub: AdminSubscription) {
    if (!token) return;
    if (expandedId === sub.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(sub.id);
    setPayments(await api.adminGetSubscriptionPayments(sub.id, token));
  }

  async function handleSweep() {
    if (!token) return;
    setSweeping(true);
    setSweepResult(null);
    try {
      const result = await api.adminRunDunningSweep(token);
      setSweepResult(`Checked ${result.checked}, applied ${result.transitions_applied} transition${result.transitions_applied === 1 ? "" : "s"}.`);
      refresh();
    } finally {
      setSweeping(false);
    }
  }

  return (
    <section className={sectionClass}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Subscriptions</h2>
        <div className="flex flex-wrap items-center gap-2">
          <button onClick={handleSweep} disabled={sweeping} className={btnSmall}>
            {sweeping ? "Running…" : "Run dunning sweep"}
          </button>
        </div>
      </div>
      {sweepResult && <p className="mt-2 text-xs text-zinc-500">{sweepResult}</p>}
      <p className="mt-1 text-xs text-zinc-400">
        There's no cron in this app yet — payment-failed reminders and downgrade notices only go
        out when this sweep runs. Wire an external scheduler (a daily cron hitting{" "}
        <code>/admin/billing/run-dunning-sweep</code>) to automate it, or trigger it manually here.
      </p>

      <div className="mt-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as SubscriptionStatusCode | "")}
          className={`${inputClass} w-auto`}
        >
          <option value="">All statuses</option>
          <option value="trialing">Trialing</option>
          <option value="active">Active</option>
          <option value="past_due">Past due</option>
          <option value="canceled">Canceled</option>
          <option value="expired">Expired</option>
        </select>
      </div>

      <ul className="mt-4 flex flex-col gap-2">
        {subs.map((s) => (
          <li key={s.id} className="rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-50">
                  {s.subscriber_name} <span className="font-normal text-zinc-500">— {s.subscriber_email}</span>
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <span className={badgeClass("neutral")}>{s.plan === "talent_premium" ? "Talent" : "Recruiter"}</span>
                  <span className={badgeClass(SUBSCRIPTION_STATUS_TONE[s.status])}>{s.status.replace("_", " ")}</span>
                  <span className="text-xs text-zinc-500">
                    LKR {s.effective_price_lkr.toLocaleString()}/{s.billing_cycle === "annual" ? "yr" : "mo"}
                  </span>
                  {s.cancel_at_period_end && <span className={badgeClass("warning")}>cancels at period end</span>}
                  {s.discount_percent && <span className={badgeClass("info")}>{s.discount_percent}% off</span>}
                </div>
                {s.cancellation_reason_category && (
                  <p className="mt-1 text-xs text-zinc-500">
                    Cancellation reason: {s.cancellation_reason_category.replace("_", " ")}
                    {s.cancellation_reason_detail ? ` — "${s.cancellation_reason_detail}"` : ""}
                  </p>
                )}
              </div>
              <button onClick={() => toggleExpand(s)} className={btnSmall}>
                {expandedId === s.id ? "Hide payments" : "View payments"}
              </button>
            </div>

            {expandedId === s.id && (
              <div className="mt-3 border-t border-zinc-200 pt-3 dark:border-zinc-800">
                {payments.length === 0 ? (
                  <p className="text-xs text-zinc-500">No payments recorded yet.</p>
                ) : (
                  <ul className="flex flex-col gap-1.5">
                    {payments.map((p) => (
                      <li key={p.id} className="flex items-center justify-between gap-2 text-xs text-zinc-600 dark:text-zinc-400">
                        <span>{new Date(p.created_at).toLocaleDateString()}</span>
                        <span
                          className={badgeClass(p.status === "succeeded" ? "success" : p.status === "failed" ? "warning" : "neutral")}
                        >
                          {p.status}
                        </span>
                        <span className="font-semibold text-zinc-900 dark:text-zinc-50">LKR {p.amount_lkr.toLocaleString()}</span>
                        {p.failure_reason && <span className="text-zinc-400">{p.failure_reason}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </li>
        ))}
        {subs.length === 0 && <p className="text-sm text-zinc-500">No subscriptions match this filter.</p>}
      </ul>
    </section>
  );
}

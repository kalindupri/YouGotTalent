"use client";

import { useEffect, useState } from "react";
import { CancellationReasonCode, Subscription, api } from "@/lib/api";
import { btnPrimary, btnSecondary, btnSmall, inputClass, labelClass } from "@/lib/ui";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

const REASON_OPTIONS: { value: CancellationReasonCode; label: string }[] = [
  { value: "too_expensive", label: "It's too expensive" },
  { value: "not_using_enough", label: "I'm not using it enough" },
  { value: "missing_features", label: "It's missing features I need" },
  { value: "switching_platform", label: "I'm switching to another platform" },
  { value: "temporary_pause", label: "Just a temporary pause" },
  { value: "other", label: "Other" },
];

type FlowStep = "closed" | "offer" | "reason" | "done";

export default function BillingStatusPanel({
  token,
  onCanceled,
  refreshKey,
}: {
  token: string;
  onCanceled?: () => void;
  // Bumped by the parent (e.g. with the profile's tier) whenever a subscription may have
  // changed outside this component — MembershipCard's "Start free trial" flips the profile's
  // tier via a sibling action this panel has no other way to hear about, so without this the
  // panel stays stuck showing no subscription until the page is manually reloaded.
  refreshKey?: string | number;
}) {
  const [sub, setSub] = useState<Subscription | null | undefined>(undefined);
  const [reactivating, setReactivating] = useState(false);
  const [step, setStep] = useState<FlowStep>("closed");
  const [offerAvailable, setOfferAvailable] = useState<{ percent: number; months: number } | null>(null);
  const [reason, setReason] = useState<CancellationReasonCode>("too_expensive");
  const [detail, setDetail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    api
      .getMyBilling(token)
      .then(setSub)
      .catch(() => setSub(null));
  }

  useEffect(refresh, [token, refreshKey]);

  async function handleReactivate() {
    setReactivating(true);
    try {
      setSub(await api.reactivateMySubscription(token));
    } finally {
      setReactivating(false);
    }
  }

  async function openCancelFlow() {
    setError(null);
    setBusy(true);
    try {
      const offer = await api.getRetentionOffer(token);
      if (offer.available) {
        setOfferAvailable({ percent: offer.discount_percent, months: offer.discount_months });
        setStep("offer");
      } else {
        setStep("reason");
      }
    } finally {
      setBusy(false);
    }
  }

  async function acceptOffer() {
    setBusy(true);
    setError(null);
    try {
      setSub(await api.acceptRetentionOffer(token));
      setStep("done");
    } catch {
      setError("Could not apply the discount — please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function confirmCancellation() {
    setBusy(true);
    setError(null);
    try {
      setSub(await api.cancelMySubscription({ reason_category: reason, reason_detail: detail || undefined }, token));
      setStep("done");
      onCanceled?.();
    } catch {
      setError("Could not schedule the cancellation — please try again.");
    } finally {
      setBusy(false);
    }
  }

  function closeFlow() {
    setStep("closed");
    setDetail("");
    setError(null);
  }

  if (!sub) return null;

  const cyclePrice = `LKR ${sub.effective_price_lkr.toLocaleString()}/${sub.billing_cycle === "annual" ? "yr" : "mo"}`;
  const hasDiscount = sub.discount_percent && sub.discount_expires_at && sub.effective_price_lkr < sub.price_lkr;

  return (
    <div className="mt-3 rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs dark:border-zinc-800 dark:bg-zinc-900/60">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-zinc-600 dark:text-zinc-400">
          {sub.status === "trialing" && sub.trial_end && <>Free trial — ends {formatDate(sub.trial_end)}</>}
          {sub.status === "active" && sub.cancel_at_period_end && sub.current_period_end && (
            <>Cancels on {formatDate(sub.current_period_end)} — you'll keep Premium until then.</>
          )}
          {sub.status === "active" && !sub.cancel_at_period_end && sub.current_period_end && (
            <>
              Renews {formatDate(sub.current_period_end)} · {cyclePrice}
              {hasDiscount && sub.discount_expires_at && (
                <> · {sub.discount_percent}% off until {formatDate(sub.discount_expires_at)}</>
              )}
            </>
          )}
          {sub.status === "past_due" && <>Payment issue on your last renewal — please update your billing details soon.</>}
          {sub.status === "canceled" && <>Subscription canceled{sub.canceled_at ? ` on ${formatDate(sub.canceled_at)}` : ""}.</>}
          {sub.status === "expired" && <>Your trial or billing period has ended.</>}
          {sub.status === "pending" && <>Checkout in progress…</>}
        </p>
        <div className="flex gap-2">
          {sub.status === "active" && sub.cancel_at_period_end && (
            <button onClick={handleReactivate} disabled={reactivating} className={btnSmall}>
              {reactivating ? "Reactivating…" : "Reactivate"}
            </button>
          )}
          {(sub.status === "active" || sub.status === "past_due") && !sub.cancel_at_period_end && (
            <button onClick={openCancelFlow} disabled={busy} className={btnSmall}>
              Cancel subscription
            </button>
          )}
        </div>
      </div>

      {step !== "closed" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={closeFlow}>
          <div
            className="w-full max-w-sm rounded-xl border border-zinc-200 bg-white p-5 text-sm normal-case shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
            onClick={(e) => e.stopPropagation()}
          >
            {step === "offer" && offerAvailable && (
              <div className="flex flex-col gap-3">
                <h3 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">Wait — before you go</h3>
                <p className="text-zinc-600 dark:text-zinc-400">
                  Stay on Premium and get <strong>{offerAvailable.percent}% off</strong> for the next{" "}
                  {offerAvailable.months} months.
                </p>
                {error && <p className="text-red-600">{error}</p>}
                <div className="flex flex-wrap justify-end gap-2">
                  <button onClick={() => setStep("reason")} disabled={busy} className={btnSecondary}>
                    No thanks, cancel
                  </button>
                  <button onClick={acceptOffer} disabled={busy} className={btnPrimary}>
                    {busy ? "Applying…" : `Claim ${offerAvailable.percent}% off`}
                  </button>
                </div>
              </div>
            )}

            {step === "reason" && (
              <div className="flex flex-col gap-3">
                <h3 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">Sorry to see you go</h3>
                <p className="text-zinc-500">Help us improve — why are you canceling?</p>
                <label className={labelClass}>
                  Reason
                  <select value={reason} onChange={(e) => setReason(e.target.value as CancellationReasonCode)} className={inputClass}>
                    {REASON_OPTIONS.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className={labelClass}>
                  Anything else? (optional)
                  <textarea value={detail} onChange={(e) => setDetail(e.target.value)} rows={3} className={inputClass} />
                </label>
                {error && <p className="text-red-600">{error}</p>}
                <div className="flex flex-wrap justify-end gap-2">
                  <button onClick={closeFlow} disabled={busy} className={btnSecondary}>
                    Never mind
                  </button>
                  <button onClick={confirmCancellation} disabled={busy} className={btnPrimary}>
                    {busy ? "Canceling…" : "Confirm cancellation"}
                  </button>
                </div>
              </div>
            )}

            {step === "done" && (
              <div className="flex flex-col gap-3">
                <h3 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">
                  {sub.discount_percent ? "Discount applied!" : "Cancellation scheduled"}
                </h3>
                <p className="text-zinc-600 dark:text-zinc-400">
                  {sub.discount_percent
                    ? `You're all set — ${sub.discount_percent}% off is now active.`
                    : sub.current_period_end
                      ? `You'll keep Premium until ${formatDate(sub.current_period_end)}. You can reactivate any time before then.`
                      : "Your subscription will end at the close of your current billing period."}
                </p>
                <div className="flex justify-end">
                  <button onClick={closeFlow} className={btnPrimary}>
                    Got it
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

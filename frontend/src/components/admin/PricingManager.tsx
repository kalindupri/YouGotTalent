"use client";

import { FormEvent, useEffect, useState } from "react";
import { AdminPricingOverview, SubscriptionPlanCode, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnPrimary, inputClass, labelClass, sectionClass } from "@/lib/ui";

const PLAN_LABELS: Record<SubscriptionPlanCode, string> = {
  talent_premium: "Talent Premium",
  recruiter_premium: "Recruiter Premium",
};

function PlanPriceEditor({
  plan,
  currentMonthly,
  currentAnnual,
  onSaved,
}: {
  plan: SubscriptionPlanCode;
  currentMonthly: number;
  currentAnnual: number;
  onSaved: (overview: AdminPricingOverview) => void;
}) {
  const { token } = useAuth();
  const [value, setValue] = useState(String(currentMonthly));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setValue(String(currentMonthly));
  }, [currentMonthly]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    const monthly_price_lkr = Number(value);
    if (!monthly_price_lkr || monthly_price_lkr <= 0) {
      setError("Enter a price greater than 0.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const overview = await api.adminSetPricing({ plan, monthly_price_lkr }, token);
      onSaved(overview);
    } catch {
      setError("Could not update the price.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
      <p className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">{PLAN_LABELS[plan]}</p>
      <p className="mt-1 text-sm text-zinc-500">
        Currently LKR {currentMonthly.toLocaleString()}/mo · LKR {currentAnnual.toLocaleString()}/yr
      </p>
      <form onSubmit={handleSubmit} className="mt-3 flex flex-wrap items-end gap-3">
        <label className={labelClass}>
          New monthly price (LKR)
          <input
            type="number"
            min={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className={`${inputClass} w-40`}
          />
        </label>
        <button type="submit" disabled={saving} className={btnPrimary}>
          {saving ? "Saving…" : "Update price"}
        </button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}

export default function PricingManager() {
  const { token } = useAuth();
  const [overview, setOverview] = useState<AdminPricingOverview | null>(null);

  function refresh() {
    if (!token) return;
    api.adminGetPricing(token).then(setOverview).catch(() => {});
  }

  useEffect(refresh, [token]);

  return (
    <div className="flex flex-col gap-6">
      <section className={sectionClass}>
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Current pricing</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Changing a price only affects new signups from this point on — everyone already subscribed keeps the
          price they signed up at for as long as they stay subscribed.
        </p>
        {overview && (
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <PlanPriceEditor
              plan="talent_premium"
              currentMonthly={overview.current.talent_premium_monthly_lkr}
              currentAnnual={overview.current.talent_premium_annual_lkr}
              onSaved={setOverview}
            />
            <PlanPriceEditor
              plan="recruiter_premium"
              currentMonthly={overview.current.recruiter_premium_monthly_lkr}
              currentAnnual={overview.current.recruiter_premium_annual_lkr}
              onSaved={setOverview}
            />
          </div>
        )}
      </section>

      <section className={sectionClass}>
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Price history</h2>
        <ul className="mt-4 flex flex-col gap-2">
          {overview?.history.map((v) => (
            <li
              key={v.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800"
            >
              <div className="flex items-center gap-2">
                <span className={badgeClass("neutral")}>{PLAN_LABELS[v.plan]}</span>
                <span className="font-semibold text-zinc-900 dark:text-zinc-50">LKR {v.monthly_price_lkr.toLocaleString()}/mo</span>
              </div>
              <div className="text-xs text-zinc-500">
                {new Date(v.created_at).toLocaleString()} {v.created_by_name ? `· by ${v.created_by_name}` : "· initial default"}
              </div>
            </li>
          ))}
          {overview && overview.history.length === 0 && <p className="text-sm text-zinc-500">No price changes recorded yet.</p>}
        </ul>
      </section>
    </div>
  );
}

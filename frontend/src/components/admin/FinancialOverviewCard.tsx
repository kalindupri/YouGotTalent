"use client";

import { useEffect, useState } from "react";
import { FinancialOverview, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { inputClass, labelClass, sectionClass } from "@/lib/ui";

export default function FinancialOverviewCard() {
  const { token } = useAuth();
  const [overview, setOverview] = useState<FinancialOverview | null>(null);
  const [talentPrice, setTalentPrice] = useState("");
  const [recruiterPrice, setRecruiterPrice] = useState("");

  useEffect(() => {
    if (!token) return;
    api
      .adminGetFinancialOverview(token)
      .then((data) => {
        setOverview(data);
        setTalentPrice(String(data.price_per_premium_talent));
        setRecruiterPrice(String(data.price_per_premium_recruiter));
      })
      .catch(() => {});
  }, [token]);

  if (!overview) {
    return (
      <section className={sectionClass}>
        <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Financial overview</h2>
        <p className="mt-2 text-sm text-zinc-500">Loading…</p>
      </section>
    );
  }

  const whatIfRevenue =
    overview.premium_talents * (Number(talentPrice) || 0) + overview.premium_recruiters * (Number(recruiterPrice) || 0);

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Financial overview</h2>
      <p className="mt-1 text-sm text-zinc-500">
        Real revenue comes from active (non-trial) subscriptions. Trialing subscribers count
        toward premium totals below but haven&apos;t paid anything yet.
      </p>

      <div className="mt-4 rounded-xl border-2 border-rose-500 bg-rose-50 p-4 dark:bg-rose-950/20">
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          Real monthly revenue: {overview.currency} {overview.real_monthly_revenue_lkr.toLocaleString()}
        </p>
        <p className="mt-1 text-xs text-zinc-500">
          {overview.paying_subscriptions} paying subscription{overview.paying_subscriptions === 1 ? "" : "s"} ·{" "}
          {overview.trialing_subscriptions} on a free trial (not yet counted)
        </p>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
          <p className="font-heading text-2xl font-black text-rose-600">{overview.premium_talents}</p>
          <p className="mt-1 text-xs text-zinc-500">Premium talents</p>
        </div>
        <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
          <p className="font-heading text-2xl font-black text-zinc-500">{overview.free_talents}</p>
          <p className="mt-1 text-xs text-zinc-500">Free talents</p>
        </div>
        <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
          <p className="font-heading text-2xl font-black text-rose-600">{overview.premium_recruiters}</p>
          <p className="mt-1 text-xs text-zinc-500">Premium recruiters</p>
        </div>
        <div className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
          <p className="font-heading text-2xl font-black text-zinc-500">{overview.free_recruiters}</p>
          <p className="mt-1 text-xs text-zinc-500">Free recruiters</p>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          Projected monthly revenue if every premium account (including trials) were paying: {overview.currency}{" "}
          {overview.estimated_monthly_revenue.toLocaleString()}
        </p>
        <p className="mt-1 text-xs text-zinc-500">
          ({overview.currency} {overview.price_per_premium_talent.toLocaleString()} / premium talent,{" "}
          {overview.currency} {overview.price_per_premium_recruiter.toLocaleString()} / premium recruiter)
        </p>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <label className={labelClass}>
            What if: price per premium talent
            <input
              type="number"
              min={0}
              value={talentPrice}
              onChange={(e) => setTalentPrice(e.target.value)}
              className={`${inputClass} w-40`}
            />
          </label>
          <label className={labelClass}>
            What if: price per premium recruiter
            <input
              type="number"
              min={0}
              value={recruiterPrice}
              onChange={(e) => setRecruiterPrice(e.target.value)}
              className={`${inputClass} w-40`}
            />
          </label>
        </div>
        <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
          At these prices:{" "}
          <span className="font-semibold text-zinc-900 dark:text-zinc-50">
            {overview.currency} {whatIfRevenue.toLocaleString()}
          </span>{" "}
          / month
        </p>
      </div>
    </section>
  );
}

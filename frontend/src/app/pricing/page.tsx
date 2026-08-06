"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Check, Crown, Sparkles } from "lucide-react";
import { ApiError, BillingCycle, CurrentPricing, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { redirectToCheckout } from "@/lib/billing";
import { btnPrimary, btnSecondary, eyebrowClass } from "@/lib/ui";

const TALENT_FREE_FEATURES = ["Full public profile", "Unlimited browsing & applications", "3 portfolio items, 1 audition video", "Standard search ranking", "Work calendar & e-signature", "Application seen/not-seen status"];
const TALENT_PREMIUM_FEATURES = [
  "Unlimited portfolio items & 5 audition videos",
  "Boosted search placement + verified badge priority",
  "See who viewed your profile",
  "Exact read-receipt times on your applications",
  "Apply to Premium-talent-only exclusive talent hunts",
  "Rotating spotlight on the homepage (once verified)",
];
const RECRUITER_FREE_FEATURES = ["2 open talent hunts at a time", "Full applicant tracking board", "Standard listing placement", "Work calendar & e-signature"];
const RECRUITER_PREMIUM_FEATURES = [
  "Unlimited open postings",
  "AI-assisted match scoring on every applicant",
  "Talent CRM — save candidates into named lists",
  "Bulk-invite talent to a talent hunt",
  "Early access to new talent sign-ups",
  "Post Premium-talent-only exclusive calls",
  "Automatic \"Featured\" placement",
  "Saved searches with alerts",
  "Recruiter analytics dashboard",
];

export default function PricingPage() {
  const { user, token } = useAuth();
  const [cycle, setCycle] = useState<BillingCycle>("monthly");
  const [loadingPlan, setLoadingPlan] = useState<"talent" | "recruiter" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pricing, setPricing] = useState<CurrentPricing | null>(null);

  useEffect(() => {
    api.getPricing().then(setPricing).catch(() => {});
  }, []);

  async function subscribe(plan: "talent" | "recruiter") {
    if (!token) return;
    setLoadingPlan(plan);
    setError(null);
    try {
      const session = await api.startCheckout(cycle, token);
      redirectToCheckout(session);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start checkout.");
      setLoadingPlan(null);
    }
  }

  return (
    <main className="flex flex-1 flex-col">
      <section className="relative overflow-hidden bg-zinc-950 pb-16 pt-20">
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:48px_48px]" />
        <div className="relative mx-auto flex max-w-4xl flex-col items-center px-6 text-center">
          <span className={eyebrowClass}>
            <Sparkles className="mr-1 inline h-3 w-3" /> Simple, honest pricing
          </span>
          <h1 className="mt-6 font-heading text-4xl font-black uppercase leading-tight tracking-tight text-white sm:text-5xl">
            Free to start. <span className="text-rose-500">Fair to grow.</span>
          </h1>
          <p className="mt-4 max-w-xl text-zinc-400">
            Browsing, applying, and your first talent hunt are always free. Premium is founding-member
            pricing — locked in for as long as you stay subscribed.
          </p>

          <div className="mt-8 inline-flex rounded-full border border-zinc-700 bg-zinc-900 p-1 text-sm font-semibold">
            <button
              onClick={() => setCycle("monthly")}
              className={`rounded-full px-4 py-1.5 transition-colors ${cycle === "monthly" ? "bg-rose-600 text-white" : "text-zinc-400"}`}
            >
              Monthly
            </button>
            <button
              onClick={() => setCycle("annual")}
              className={`rounded-full px-4 py-1.5 transition-colors ${cycle === "annual" ? "bg-rose-600 text-white" : "text-zinc-400"}`}
            >
              Annual — 2 months free
            </button>
          </div>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-5xl gap-8 px-6 py-16 sm:grid-cols-2">
        <PricingColumn
          title="For talent"
          roleLabel="talent"
          freePrice="LKR 0"
          premiumPrice={
            pricing
              ? cycle === "annual"
                ? `LKR ${pricing.talent_premium_annual_lkr.toLocaleString()}/yr`
                : `LKR ${pricing.talent_premium_monthly_lkr.toLocaleString()}/mo`
              : "…"
          }
          freeFeatures={TALENT_FREE_FEATURES}
          premiumFeatures={TALENT_PREMIUM_FEATURES}
          canSubscribe={!user || user.role === "talent"}
          loading={loadingPlan === "talent"}
          onSubscribe={() => subscribe("talent")}
          loggedIn={!!token}
        />
        <PricingColumn
          title="For recruiters"
          roleLabel="recruiter"
          freePrice="LKR 0"
          premiumPrice={
            pricing
              ? cycle === "annual"
                ? `LKR ${pricing.recruiter_premium_annual_lkr.toLocaleString()}/yr`
                : `LKR ${pricing.recruiter_premium_monthly_lkr.toLocaleString()}/mo`
              : "…"
          }
          freeFeatures={RECRUITER_FREE_FEATURES}
          premiumFeatures={RECRUITER_PREMIUM_FEATURES}
          canSubscribe={!user || user.role === "recruiter"}
          loading={loadingPlan === "recruiter"}
          onSubscribe={() => subscribe("recruiter")}
          loggedIn={!!token}
        />
      </section>

      {error && <p className="mx-auto -mt-8 mb-8 max-w-5xl px-6 text-sm text-red-600">{error}</p>}
    </main>
  );
}

function PricingColumn({
  title,
  roleLabel,
  freePrice,
  premiumPrice,
  freeFeatures,
  premiumFeatures,
  canSubscribe,
  loggedIn,
  loading,
  onSubscribe,
}: {
  title: string;
  roleLabel: string;
  freePrice: string;
  premiumPrice: string;
  freeFeatures: string[];
  premiumFeatures: string[];
  canSubscribe: boolean;
  loggedIn: boolean;
  loading: boolean;
  onSubscribe: () => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <h2 className="font-heading text-xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">{title}</h2>

      <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
        <p className="text-sm font-bold uppercase tracking-wide text-zinc-500">Free</p>
        <p className="mt-1 font-heading text-2xl font-black text-zinc-900 dark:text-zinc-50">{freePrice}</p>
        <ul className="mt-4 flex flex-col gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          {freeFeatures.map((f) => (
            <li key={f} className="flex items-start gap-2">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> {f}
            </li>
          ))}
        </ul>
        {!loggedIn && (
          <Link href="/register" className={`mt-5 w-full ${btnSecondary}`}>
            Sign up free
          </Link>
        )}
      </div>

      <div className="rounded-xl border-2 border-rose-500 bg-white p-5 shadow-sm dark:bg-zinc-900">
        <p className="flex items-center gap-1 text-sm font-bold uppercase tracking-wide text-rose-600">
          <Crown className="h-3.5 w-3.5" fill="currentColor" strokeWidth={0} /> Premium
        </p>
        <p className="mt-1 font-heading text-2xl font-black text-zinc-900 dark:text-zinc-50">{premiumPrice}</p>
        <ul className="mt-4 flex flex-col gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          {premiumFeatures.map((f) => (
            <li key={f} className="flex items-start gap-2">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-rose-500" /> {f}
            </li>
          ))}
        </ul>

        {!loggedIn ? (
          <Link href="/register" className={`mt-5 w-full ${btnPrimary}`}>
            Create an account
          </Link>
        ) : canSubscribe ? (
          <button onClick={onSubscribe} disabled={loading} className={`mt-5 w-full ${btnPrimary}`}>
            {loading ? "Starting checkout…" : "Subscribe"}
          </button>
        ) : (
          <p className="mt-5 text-xs text-zinc-400">Sign in with a {roleLabel} account to subscribe to this plan.</p>
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Clock } from "lucide-react";
import { Subscription, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnPrimary } from "@/lib/ui";

export default function BillingSuccessPage() {
  const { token } = useAuth();
  const [sub, setSub] = useState<Subscription | null | undefined>(undefined);

  useEffect(() => {
    if (!token) return;
    api.getMyBilling(token).then(setSub).catch(() => setSub(null));
  }, [token]);

  const isActive = sub?.status === "active";

  return (
    <main className="mx-auto flex w-full max-w-lg flex-1 flex-col items-center justify-center px-6 py-24 text-center">
      {isActive ? (
        <>
          <CheckCircle2 className="h-12 w-12 text-emerald-500" />
          <h1 className="mt-4 font-heading text-2xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
            You&apos;re on Premium
          </h1>
          <p className="mt-2 text-sm text-zinc-500">Your subscription is active. Head back to your dashboard to see what&apos;s unlocked.</p>
        </>
      ) : (
        <>
          <Clock className="h-12 w-12 text-amber-500" />
          <h1 className="mt-4 font-heading text-2xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
            Confirming your payment
          </h1>
          <p className="mt-2 text-sm text-zinc-500">
            This can take a moment for card payments. If your dashboard still shows Free after a few
            minutes, contact support.
          </p>
        </>
      )}
      <Link href="/dashboard" className={`mt-6 ${btnPrimary}`}>
        Go to dashboard
      </Link>
    </main>
  );
}

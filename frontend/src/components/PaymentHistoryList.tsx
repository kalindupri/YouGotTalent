"use client";

import { useEffect, useState } from "react";
import { Payment, api } from "@/lib/api";
import { badgeClass } from "@/lib/ui";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function statusTone(status: Payment["status"]): "success" | "warning" | "neutral" {
  if (status === "succeeded") return "success";
  if (status === "failed") return "warning";
  return "neutral";
}

export default function PaymentHistoryList({ token }: { token: string }) {
  const [payments, setPayments] = useState<Payment[] | null>(null);

  useEffect(() => {
    api
      .getMyPayments(token)
      .then(setPayments)
      .catch(() => setPayments([]));
  }, [token]);

  if (!payments || payments.length === 0) return null;

  return (
    <div className="mt-3">
      <p className="text-xs font-bold uppercase tracking-wide text-zinc-500">Billing history</p>
      <ul className="mt-2 flex flex-col gap-1.5">
        {payments.map((p) => (
          <li key={p.id} className="flex items-center justify-between gap-2 text-xs text-zinc-600 dark:text-zinc-400">
            <span>{formatDate(p.created_at)}</span>
            <span className={badgeClass(statusTone(p.status))}>{p.status}</span>
            <span className="font-semibold text-zinc-900 dark:text-zinc-50">LKR {p.amount_lkr.toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

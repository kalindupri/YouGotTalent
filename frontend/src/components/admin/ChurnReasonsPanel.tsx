"use client";

import { useEffect, useState } from "react";
import { ChurnReasons, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { sectionClass } from "@/lib/ui";

const CHURN_REASON_LABELS: Record<string, string> = {
  too_expensive: "Too expensive",
  not_using_enough: "Not using it enough",
  missing_features: "Missing features",
  switching_platform: "Switching platform",
  temporary_pause: "Temporary pause",
  other: "Other",
};

export default function ChurnReasonsPanel() {
  const { token } = useAuth();
  const [reasons, setReasons] = useState<ChurnReasons | null>(null);

  useEffect(() => {
    if (!token) return;
    api.adminGetChurnReasons(token).then(setReasons).catch(() => {});
  }, [token]);

  const total = reasons ? Object.values(reasons.counts).reduce((sum, n) => sum + n, 0) : 0;

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Why customers leave</h2>
      {!reasons || total === 0 ? (
        <p className="mt-2 text-sm text-zinc-500">No cancellations recorded yet.</p>
      ) : (
        <>
          <ul className="mt-4 flex flex-col gap-2">
            {Object.entries(reasons.counts)
              .filter(([, count]) => count > 0)
              .sort(([, a], [, b]) => b - a)
              .map(([reason, count]) => (
                <li key={reason} className="flex items-center gap-3">
                  <span className="w-40 shrink-0 text-sm text-zinc-700 dark:text-zinc-300">{CHURN_REASON_LABELS[reason] ?? reason}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                    <div className="h-full rounded-full bg-rose-500" style={{ width: `${(count / total) * 100}%` }} />
                  </div>
                  <span className="w-6 shrink-0 text-right text-sm font-semibold text-zinc-900 dark:text-zinc-50">{count}</span>
                </li>
              ))}
          </ul>
          {reasons.recent_details.length > 0 && (
            <div className="mt-4 border-t border-zinc-200 pt-3 dark:border-zinc-800">
              <p className="text-xs font-bold uppercase tracking-wide text-zinc-500">Recent comments</p>
              <ul className="mt-2 flex flex-col gap-1.5">
                {reasons.recent_details.map((detail, i) => (
                  <li key={i} className="text-sm italic text-zinc-600 dark:text-zinc-400">
                    &ldquo;{detail}&rdquo;
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}

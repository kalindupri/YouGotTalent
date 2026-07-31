"use client";

import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { RecruiterProfile, TalentProfile, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnSmall, btnSmallPrimary, categoryBadgeClass, formatCategory, sectionClass } from "@/lib/ui";

export default function VerificationQueue() {
  const { token } = useAuth();
  const [talents, setTalents] = useState<TalentProfile[]>([]);
  const [recruiters, setRecruiters] = useState<RecruiterProfile[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);

  function refresh() {
    if (!token) return;
    api.adminListPendingTalentVerifications(token).then(setTalents).catch(() => {});
    api.adminListPendingRecruiterVerifications(token).then(setRecruiters).catch(() => {});
  }

  useEffect(refresh, [token]);

  async function handleTalent(id: string, action: "approve" | "reject") {
    if (!token) return;
    setBusyId(id);
    try {
      if (action === "approve") await api.adminApproveTalentVerification(id, token);
      else await api.adminRejectTalentVerification(id, token);
      setTalents((prev) => prev.filter((t) => t.id !== id));
    } finally {
      setBusyId(null);
    }
  }

  async function handleRecruiter(id: string, action: "approve" | "reject") {
    if (!token) return;
    setBusyId(id);
    try {
      if (action === "approve") await api.adminApproveRecruiterVerification(id, token);
      else await api.adminRejectRecruiterVerification(id, token);
      setRecruiters((prev) => prev.filter((r) => r.id !== id));
    } finally {
      setBusyId(null);
    }
  }

  const empty = talents.length === 0 && recruiters.length === 0;

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Verification requests</h2>
      {empty ? (
        <p className="mt-2 text-sm text-zinc-500">No pending verification requests.</p>
      ) : (
        <ul className="mt-4 flex flex-col gap-2">
          {talents.map((t) => (
            <li
              key={t.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800"
            >
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-50">{t.display_name}</p>
                <div className="mt-1 flex items-center gap-2">
                  <span className={badgeClass("info")}>Talent</span>
                  <span className={categoryBadgeClass(t.category)}>{formatCategory(t.category)}</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  disabled={busyId === t.id}
                  onClick={() => handleTalent(t.id, "approve")}
                  className={btnSmallPrimary}
                >
                  <Check className="h-3.5 w-3.5" /> Approve
                </button>
                <button disabled={busyId === t.id} onClick={() => handleTalent(t.id, "reject")} className={btnSmall}>
                  <X className="h-3.5 w-3.5" /> Reject
                </button>
              </div>
            </li>
          ))}
          {recruiters.map((r) => (
            <li
              key={r.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800"
            >
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-50">{r.company_name}</p>
                <span className={badgeClass("warning")}>Recruiter</span>
              </div>
              <div className="flex gap-2">
                <button
                  disabled={busyId === r.id}
                  onClick={() => handleRecruiter(r.id, "approve")}
                  className={btnSmallPrimary}
                >
                  <Check className="h-3.5 w-3.5" /> Approve
                </button>
                <button disabled={busyId === r.id} onClick={() => handleRecruiter(r.id, "reject")} className={btnSmall}>
                  <X className="h-3.5 w-3.5" /> Reject
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

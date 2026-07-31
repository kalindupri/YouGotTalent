"use client";

import { useEffect, useState } from "react";
import { AdminCastingCall, CastingCallStatus, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnSmall, categoryBadgeClass, formatCategory, inputClass, sectionClass, statusTone } from "@/lib/ui";

export default function CastingCallModeration() {
  const { token } = useAuth();
  const [calls, setCalls] = useState<AdminCastingCall[]>([]);
  const [statusFilter, setStatusFilter] = useState<CastingCallStatus | "">("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api.adminListCastingCalls({ status: statusFilter || undefined }, token).then(setCalls).catch(() => {});
  }, [statusFilter, token]);

  async function toggleStatus(call: AdminCastingCall) {
    if (!token) return;
    const nextStatus: CastingCallStatus = call.status === "open" ? "closed" : "open";
    setBusyId(call.id);
    try {
      const updated = await api.adminSetCastingCallStatus(call.id, nextStatus, token);
      setCalls((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Talent hunts</h2>
      <div className="mt-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as CastingCallStatus | "")}
          className={`${inputClass} w-auto`}
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <ul className="mt-4 flex flex-col gap-2">
        {calls.map((c) => (
          <li key={c.id} className="rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-50">{c.title}</p>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <span className={categoryBadgeClass(c.category)}>{formatCategory(c.category)}</span>
                  <span className={badgeClass(statusTone(c.status))}>{c.status}</span>
                  <span className="text-xs text-zinc-500">by {c.recruiter_company_name}</span>
                  <span className="text-xs text-zinc-500">
                    {c.application_count} application{c.application_count === 1 ? "" : "s"} · {c.invitation_count} invitation
                    {c.invitation_count === 1 ? "" : "s"}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setExpandedId((prev) => (prev === c.id ? null : c.id))} className={btnSmall}>
                  {expandedId === c.id ? "Hide details" : "View details"}
                </button>
                <button disabled={busyId === c.id} onClick={() => toggleStatus(c)} className={btnSmall}>
                  {c.status === "open" ? "Close" : "Reopen"}
                </button>
              </div>
            </div>

            {expandedId === c.id && (
              <div className="mt-3 flex flex-col gap-2 border-t border-zinc-200 pt-3 text-xs text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
                <p className="whitespace-pre-wrap">{c.description}</p>
                <p>Location: {c.location ?? "—"}</p>
                <p>Compensation: {c.compensation ?? "—"}</p>
                <p>Application deadline: {c.application_deadline ?? "—"}</p>
                {c.tags && c.tags.length > 0 && <p>Tags: {c.tags.join(", ")}</p>}
                {c.shoot_details && <p>Dates &amp; locations: {c.shoot_details}</p>}
                {c.audition_brief && <p>What to perform: {c.audition_brief}</p>}
                {c.roles.length > 0 && (
                  <div>
                    <p className="font-semibold text-zinc-700 dark:text-zinc-300">Roles</p>
                    <ul className="mt-1 flex flex-col gap-1">
                      {c.roles.map((r) => (
                        <li key={r.id}>
                          {r.title}
                          {r.criteria ? ` — ${r.criteria}` : ""}
                          {r.compensation ? ` (${r.compensation})` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </li>
        ))}
        {calls.length === 0 && <p className="text-sm text-zinc-500">No talent hunts match this filter.</p>}
      </ul>
    </section>
  );
}

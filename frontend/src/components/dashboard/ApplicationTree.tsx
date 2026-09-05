"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { Application, ApplicationStatus, CastingCallRole } from "@/lib/api";
import { badgeClass } from "@/lib/ui";

/** Applications grouped by the role they were made for.
 *
 * The status board mixes every role's applicants into four columns, with the role as a subtitle
 * on each card. That works for one role and stops working at two: a recruiter casting a lead and
 * a supporting part cannot see where either stands without reading every card.
 *
 * The data is already a tree -- a hunt holds roles, a role holds applications -- so this shows
 * it as one. Depth is carried by a drawn rail rather than indentation, because indentation at
 * phone width eats the names it is supposed to be organising.
 */

/** What a recruiter actually needs to distinguish, which is more than Application.status.
 *
 * `status` and the offer are separate axes: an application sits at `shortlisted` from the moment
 * it is shortlisted until both parties have signed, so an offer that has been sent, and one the
 * talent has accepted but not yet signed, are indistinguishable by status alone. Collapsing them
 * into "Shortlisted" is how a recruiter comes to believe they have a hire when they have a
 * maybe. `pending_offer_status` carries the difference and is surfaced here.
 */
function stage(a: Application): { label: string; tone: "neutral" | "success" | "warning" | "info"; dot: string } {
  if (a.status === "accepted") return { label: "Booked", tone: "success", dot: "bg-emerald-500" };
  if (a.status === "rejected") return { label: "Passed", tone: "neutral", dot: "bg-zinc-300" };
  if (a.pending_offer_status === "awaiting_signature")
    return { label: "Awaiting signature", tone: "warning", dot: "bg-amber-500" };
  if (a.pending_offer_status === "offer_sent") return { label: "Offer sent", tone: "warning", dot: "bg-amber-500" };
  if (a.status === "shortlisted") return { label: "Shortlisted", tone: "info", dot: "bg-rose-500" };
  return { label: "Pending", tone: "neutral", dot: "bg-zinc-400" };
}

const STATUS_ORDER: ApplicationStatus[] = ["accepted", "shortlisted", "pending", "rejected"];

function ApplicantRow({
  application,
  last,
  onOpen,
}: {
  application: Application;
  last: boolean;
  onOpen: (a: Application) => void;
}) {
  const s = stage(application);
  return (
    <button
      type="button"
      onClick={() => onOpen(application)}
      className="flex w-full items-stretch gap-2.5 text-left"
    >
      {/* The rail: a full-height line for every row except the last, which stops at the elbow. */}
      <span aria-hidden className="relative w-3 shrink-0">
        <span
          className={`absolute left-1.5 top-0 w-px bg-zinc-200 dark:bg-zinc-800 ${last ? "h-1/2" : "h-full"}`}
        />
        <span className="absolute left-1.5 top-1/2 h-px w-2 bg-zinc-200 dark:bg-zinc-800" />
      </span>
      <span className="flex min-h-[44px] flex-grow items-center gap-2 py-1.5">
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${s.dot}`} />
        <span className="min-w-0 flex-grow truncate text-sm font-semibold text-zinc-900 dark:text-zinc-50">
          {application.talent_display_name}
        </span>
        <span className={badgeClass(s.tone)}>{s.label}</span>
      </span>
    </button>
  );
}

export default function ApplicationTree({
  roles,
  applications,
  onOpen,
}: {
  roles: CastingCallRole[];
  applications: Application[];
  onOpen: (a: Application) => void;
}) {
  // Every role starts open: a recruiter opening this wants the picture, not a set of closed doors.
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  function toggle(roleId: string) {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(roleId)) next.delete(roleId);
      else next.add(roleId);
      return next;
    });
  }

  // An application whose role was deleted would otherwise vanish from this view entirely.
  const knownRoleIds = new Set(roles.map((r) => r.id));
  const orphans = applications.filter((a) => !knownRoleIds.has(a.role_id));

  const groups: { id: string; title: string; items: Application[] }[] = [
    ...roles.map((r) => ({
      id: r.id,
      title: r.title,
      items: applications.filter((a) => a.role_id === r.id),
    })),
    ...(orphans.length > 0 ? [{ id: "__orphans", title: "Role no longer listed", items: orphans }] : []),
  ];

  return (
    <div className="mt-4 flex flex-col gap-3">
      {groups.map((group) => {
        const open = !collapsed.has(group.id);
        const sorted = [...group.items].sort(
          (a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)
        );
        const counts = STATUS_ORDER.map((s) => ({
          status: s,
          n: group.items.filter((a) => a.status === s).length,
        })).filter((c) => c.n > 0);

        return (
          <section
            key={group.id}
            className="rounded-xl border border-zinc-200 bg-white p-3 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
          >
            <button
              type="button"
              onClick={() => toggle(group.id)}
              aria-expanded={open}
              className="flex min-h-[44px] w-full items-center gap-2 text-left"
            >
              {open ? (
                <ChevronDown className="h-4 w-4 shrink-0 text-zinc-600 dark:text-zinc-400" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0 text-zinc-600 dark:text-zinc-400" />
              )}
              <span className="flex-grow truncate text-sm font-bold text-zinc-900 dark:text-zinc-50">
                {group.title}
              </span>
              <span className={badgeClass("neutral")}>{group.items.length}</span>
            </button>

            {open && (
              <>
                {counts.length > 0 && (
                  <div className="mb-1 mt-2 flex flex-wrap gap-1.5 pl-6">
                    {counts.map((c) => (
                      <span key={c.status} className="text-xs text-zinc-500">
                        {c.n} {c.status}
                      </span>
                    ))}
                  </div>
                )}
                <div className="flex flex-col">
                  {sorted.map((a, i) => (
                    <ApplicantRow
                      key={a.id}
                      application={a}
                      last={i === sorted.length - 1}
                      onOpen={onOpen}
                    />
                  ))}
                  {sorted.length === 0 && (
                    <p className="py-2 pl-6 text-xs text-zinc-400">Nobody has applied for this role yet.</p>
                  )}
                </div>
              </>
            )}
          </section>
        );
      })}
    </div>
  );
}

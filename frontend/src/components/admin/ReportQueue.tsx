"use client";

import { useEffect, useState } from "react";
import { Check, Trash2, X } from "lucide-react";
import Link from "next/link";
import { ReportCategory, ReportStatus, ReportWithReporter, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnSmall, btnSmallPrimary, inputClass, labelClass, sectionClass } from "@/lib/ui";

const REPORT_CATEGORY_LABELS: Record<ReportCategory, string> = {
  bug: "Bug",
  spam: "Spam",
  harassment: "Harassment",
  fake_profile: "Fake profile",
  inappropriate_content: "Inappropriate content",
  other: "Other",
};

const REPORT_STATUS_TONE: Record<ReportStatus, "warning" | "info" | "success" | "neutral"> = {
  open: "warning",
  in_review: "info",
  resolved: "success",
  dismissed: "neutral",
};

function reportTargetHref(report: ReportWithReporter): string | null {
  if (!report.target_type || !report.target_id) return null;
  switch (report.target_type) {
    case "talent_profile":
      return `/talents/${report.target_id}`;
    case "recruiter_profile":
      return `/recruiters/${report.target_id}`;
    case "casting_call":
      return `/casting-calls/${report.target_id}`;
    case "title":
      return `/community/titles/${report.target_id}`;
    case "discussion_thread":
      return `/community/discussions/${report.target_id}`;
    default:
      return null;
  }
}

// Reports on these target types have a corresponding "delete the content" admin action —
// talent/recruiter/casting-call reports are instead handled via suspend/close in their own sections.
const DELETABLE_TARGET_TYPES = new Set(["title", "title_review", "discussion_thread", "discussion_reply"]);

function deleteReportedContent(targetType: string, targetId: string, token: string): Promise<void> | null {
  switch (targetType) {
    case "title":
      return api.adminDeleteTitle(targetId, token);
    case "title_review":
      return api.adminDeleteTitleReview(targetId, token);
    case "discussion_thread":
      return api.adminDeleteThread(targetId, token);
    case "discussion_reply":
      return api.adminDeleteReply(targetId, token);
    default:
      return null;
  }
}

export default function ReportQueue() {
  const { token } = useAuth();
  const [reports, setReports] = useState<ReportWithReporter[]>([]);
  const [statusFilter, setStatusFilter] = useState<ReportStatus | "">("open");
  const [categoryFilter, setCategoryFilter] = useState<ReportCategory | "">("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notesDraft, setNotesDraft] = useState<Record<string, string>>({});

  function refresh() {
    if (!token) return;
    api
      .adminListReports({ status: statusFilter || undefined, category: categoryFilter || undefined }, token)
      .then(setReports)
      .catch(() => {});
  }

  useEffect(refresh, [statusFilter, categoryFilter, token]);

  async function updateStatus(report: ReportWithReporter, nextStatus: ReportStatus) {
    if (!token) return;
    setBusyId(report.id);
    try {
      const updated = await api.adminUpdateReport(
        report.id,
        { status: nextStatus, admin_notes: notesDraft[report.id] ?? report.admin_notes ?? undefined },
        token
      );
      setReports((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } finally {
      setBusyId(null);
    }
  }

  async function handleDeleteContent(report: ReportWithReporter) {
    if (!token || !report.target_type || !report.target_id) return;
    const action = deleteReportedContent(report.target_type, report.target_id, token);
    if (!action) return;
    setBusyId(report.id);
    try {
      await action;
      await updateStatus(report, "resolved");
    } catch {
      // Content may have already been deleted — nothing to recover here.
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Reports</h2>
      <div className="mt-4 flex flex-wrap gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as ReportStatus | "")}
          className={`${inputClass} w-auto`}
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="in_review">In review</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value as ReportCategory | "")}
          className={`${inputClass} w-auto`}
        >
          <option value="">All categories</option>
          {Object.entries(REPORT_CATEGORY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <ul className="mt-4 flex flex-col gap-2">
        {reports.map((r) => {
          const targetHref = reportTargetHref(r);
          const canDeleteContent = !!r.target_type && DELETABLE_TARGET_TYPES.has(r.target_type);
          return (
            <li key={r.id} className="rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-zinc-900 dark:text-zinc-50">{r.subject}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <span className={badgeClass("neutral")}>{REPORT_CATEGORY_LABELS[r.category]}</span>
                    <span className={badgeClass(REPORT_STATUS_TONE[r.status])}>{r.status.replace("_", " ")}</span>
                    <span className="text-xs text-zinc-500">from {r.reporter_email}</span>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-zinc-600 dark:text-zinc-400">{r.description}</p>
                  {targetHref && (
                    <Link href={targetHref} target="_blank" className="mt-1 inline-block text-xs font-semibold text-rose-600 hover:underline">
                      View reported {r.target_type?.replace("_", " ")} →
                    </Link>
                  )}
                  {r.page_url && <p className="mt-1 text-xs text-zinc-500">Page: {r.page_url}</p>}
                </div>
              </div>

              <div className="mt-3 flex flex-wrap items-end gap-2">
                <label className={`${labelClass} flex-1 min-w-[200px]`}>
                  Admin notes
                  <input
                    value={notesDraft[r.id] ?? r.admin_notes ?? ""}
                    onChange={(e) => setNotesDraft((prev) => ({ ...prev, [r.id]: e.target.value }))}
                    className={inputClass}
                  />
                </label>
                <div className="flex flex-wrap gap-2">
                  {r.status !== "in_review" && (
                    <button disabled={busyId === r.id} onClick={() => updateStatus(r, "in_review")} className={btnSmall}>
                      In review
                    </button>
                  )}
                  {r.status !== "resolved" && (
                    <button disabled={busyId === r.id} onClick={() => updateStatus(r, "resolved")} className={btnSmallPrimary}>
                      <Check className="h-3.5 w-3.5" /> Resolve
                    </button>
                  )}
                  {r.status !== "dismissed" && (
                    <button disabled={busyId === r.id} onClick={() => updateStatus(r, "dismissed")} className={btnSmall}>
                      <X className="h-3.5 w-3.5" /> Dismiss
                    </button>
                  )}
                  {canDeleteContent && (
                    <button
                      disabled={busyId === r.id}
                      onClick={() => handleDeleteContent(r)}
                      className={`${btnSmall} !border-red-300 !text-red-600 hover:!border-red-500`}
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Delete content
                    </button>
                  )}
                </div>
              </div>
            </li>
          );
        })}
        {reports.length === 0 && <p className="text-sm text-zinc-500">No reports match this filter.</p>}
      </ul>
    </section>
  );
}

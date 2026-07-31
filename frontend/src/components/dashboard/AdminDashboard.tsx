"use client";

import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import Link from "next/link";
import {
  AdminCastingCall,
  AdminStats,
  AdminUserDetail,
  CastingCallStatus,
  FinancialOverview,
  RecruiterProfile,
  ReportCategory,
  ReportStatus,
  ReportWithReporter,
  TalentProfile,
  User,
  UserRole,
  api,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  badgeClass,
  btnSmall,
  btnSmallPrimary,
  categoryBadgeClass,
  formatCategory,
  inputClass,
  labelClass,
  sectionClass,
  statusTone,
} from "@/lib/ui";

export default function AdminDashboard() {
  const { token } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    if (!token) return;
    api.adminGetStats(token).then(setStats).catch(() => {});
  }, [token]);

  if (!token) return null;

  return (
    <div className="flex flex-col gap-6">
      <StatsGrid stats={stats} />
      <FinancialOverviewCard token={token} />
      <ReportQueue token={token} />
      <VerificationQueue token={token} />
      <UserManagement token={token} />
      <CastingCallModeration token={token} />
    </div>
  );
}

function StatsGrid({ stats }: { stats: AdminStats | null }) {
  const tiles: { label: string; value: number | string }[] = stats
    ? [
        { label: "Total users", value: stats.total_users },
        { label: "Talents", value: stats.total_talents },
        { label: "Recruiters", value: stats.total_recruiters },
        { label: "Verified talents", value: stats.verified_talents },
        { label: "Verified recruiters", value: stats.verified_recruiters },
        { label: "Open talent hunts", value: stats.open_casting_calls },
        { label: "Closed talent hunts", value: stats.closed_casting_calls },
        { label: "Applications", value: stats.total_applications },
        { label: "Invitations", value: stats.total_invitations },
      ]
    : [];

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Platform overview</h2>
      {!stats ? (
        <p className="mt-2 text-sm text-zinc-500">Loading…</p>
      ) : (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {tiles.map((t) => (
            <div key={t.label} className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
              <p className="font-heading text-2xl font-black text-rose-600">{t.value}</p>
              <p className="mt-1 text-xs text-zinc-500">{t.label}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function FinancialOverviewCard({ token }: { token: string }) {
  const [overview, setOverview] = useState<FinancialOverview | null>(null);
  const [talentPrice, setTalentPrice] = useState("");
  const [recruiterPrice, setRecruiterPrice] = useState("");

  useEffect(() => {
    api.adminGetFinancialOverview(token).then((data) => {
      setOverview(data);
      setTalentPrice(String(data.price_per_premium_talent));
      setRecruiterPrice(String(data.price_per_premium_recruiter));
    }).catch(() => {});
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
        No payment gateway is wired up yet — every figure here is a projection from current
        subscription counts, not real collected revenue.
      </p>

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
          Estimated monthly revenue at current pricing: {overview.currency} {overview.estimated_monthly_revenue.toLocaleString()}
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
          At these prices: <span className="font-semibold text-zinc-900 dark:text-zinc-50">{overview.currency} {whatIfRevenue.toLocaleString()}</span> / month
        </p>
      </div>
    </section>
  );
}

function VerificationQueue({ token }: { token: string }) {
  const [talents, setTalents] = useState<TalentProfile[]>([]);
  const [recruiters, setRecruiters] = useState<RecruiterProfile[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);

  function refresh() {
    api.adminListPendingTalentVerifications(token).then(setTalents).catch(() => {});
    api.adminListPendingRecruiterVerifications(token).then(setRecruiters).catch(() => {});
  }

  useEffect(refresh, [token]);

  async function handleTalent(id: string, action: "approve" | "reject") {
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

function UserManagement({ token }: { token: string }) {
  const [users, setUsers] = useState<User[]>([]);
  const [role, setRole] = useState<UserRole | "">("");
  const [q, setQ] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      api.adminListUsers({ role: role || undefined, q: q || undefined }, token).then(setUsers).catch(() => {});
    }, 250);
    return () => clearTimeout(handle);
  }, [role, q, token]);

  async function toggleActive(user: User) {
    setBusyId(user.id);
    try {
      const updated = await api.adminSetUserActive(user.id, !user.is_active, token);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch {
      // Most likely the "can't change your own status" guard — nothing to recover here.
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Users</h2>
      <div className="mt-4 flex flex-wrap gap-3">
        <input
          placeholder="Search by name or email"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={`${inputClass} max-w-xs`}
        />
        <select value={role} onChange={(e) => setRole(e.target.value as UserRole | "")} className={`${inputClass} w-auto`}>
          <option value="">All roles</option>
          <option value="talent">Talent</option>
          <option value="recruiter">Recruiter</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      <ul className="mt-4 flex flex-col gap-2">
        {users.map((u) => (
          <li key={u.id} className="rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-50">
                  {u.full_name} <span className="font-normal text-zinc-500">— {u.email}</span>
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <span className={badgeClass("neutral")}>{u.role}</span>
                  <span className={badgeClass(u.is_active ? "success" : "warning")}>
                    {u.is_active ? "active" : "suspended"}
                  </span>
                  {!u.email_verified && <span className={badgeClass("warning")}>unverified email</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setExpandedId((prev) => (prev === u.id ? null : u.id))} className={btnSmall}>
                  {expandedId === u.id ? "Hide details" : "View details"}
                </button>
                <button
                  disabled={busyId === u.id}
                  onClick={() => toggleActive(u)}
                  className={u.is_active ? btnSmall : btnSmallPrimary}
                >
                  {u.is_active ? "Suspend" : "Reactivate"}
                </button>
              </div>
            </div>
            {expandedId === u.id && <UserDetailPanel userId={u.id} token={token} />}
          </li>
        ))}
        {users.length === 0 && <p className="text-sm text-zinc-500">No users match this filter.</p>}
      </ul>
    </section>
  );
}

function UserDetailPanel({ userId, token }: { userId: string; token: string }) {
  const [detail, setDetail] = useState<AdminUserDetail | null>(null);

  useEffect(() => {
    api.adminGetUserDetail(userId, token).then(setDetail).catch(() => {});
  }, [userId, token]);

  if (!detail) {
    return <p className="mt-3 text-xs text-zinc-500">Loading account details…</p>;
  }

  return (
    <div className="mt-3 flex flex-col gap-2 border-t border-zinc-200 pt-3 text-xs text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
      <p>Phone: {detail.phone ?? "—"}</p>
      <p>Joined: {new Date(detail.created_at).toLocaleDateString()}</p>
      {detail.talent_profile && (
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
          <p className="font-semibold text-zinc-700 dark:text-zinc-300">Talent profile</p>
          <p className="mt-1">
            {detail.talent_profile.display_name} · {formatCategory(detail.talent_profile.category)} ·{" "}
            {detail.talent_profile.city ?? "no city set"}
          </p>
          <p className="mt-1">
            Tier: {detail.talent_profile.tier} · {detail.talent_profile.is_verified ? "Verified" : "Not verified"}
          </p>
        </div>
      )}
      {detail.recruiter_profile && (
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
          <p className="font-semibold text-zinc-700 dark:text-zinc-300">Recruiter profile</p>
          <p className="mt-1">
            {detail.recruiter_profile.company_name} · {detail.recruiter_profile.industry ?? "no industry set"}
          </p>
          <p className="mt-1">
            Tier: {detail.recruiter_profile.tier} · {detail.recruiter_profile.is_verified ? "Verified" : "Not verified"}
          </p>
        </div>
      )}
      {!detail.talent_profile && !detail.recruiter_profile && <p>No linked talent or recruiter profile.</p>}
    </div>
  );
}

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
    default:
      return null;
  }
}

function ReportQueue({ token }: { token: string }) {
  const [reports, setReports] = useState<ReportWithReporter[]>([]);
  const [statusFilter, setStatusFilter] = useState<ReportStatus | "">("open");
  const [categoryFilter, setCategoryFilter] = useState<ReportCategory | "">("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notesDraft, setNotesDraft] = useState<Record<string, string>>({});

  function refresh() {
    api
      .adminListReports({ status: statusFilter || undefined, category: categoryFilter || undefined }, token)
      .then(setReports)
      .catch(() => {});
  }

  useEffect(refresh, [statusFilter, categoryFilter, token]);

  async function updateStatus(report: ReportWithReporter, nextStatus: ReportStatus) {
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
                <div className="flex gap-2">
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

function CastingCallModeration({ token }: { token: string }) {
  const [calls, setCalls] = useState<AdminCastingCall[]>([]);
  const [statusFilter, setStatusFilter] = useState<CastingCallStatus | "">("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    api.adminListCastingCalls({ status: statusFilter || undefined }, token).then(setCalls).catch(() => {});
  }, [statusFilter, token]);

  async function toggleStatus(call: AdminCastingCall) {
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
                {c.shoot_details && <p>Dates & locations: {c.shoot_details}</p>}
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

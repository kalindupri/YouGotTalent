"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Play } from "lucide-react";
import { Application, ApplicationStatus, CastingCall, Invitation, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, eyebrowClass, invitationStatusTone } from "@/lib/ui";

const COLUMNS: { status: ApplicationStatus; label: string; accent: string }[] = [
  { status: "pending", label: "Pending review", accent: "bg-amber-500" },
  { status: "shortlisted", label: "Shortlisted", accent: "bg-rose-500" },
  { status: "accepted", label: "Accepted", accent: "bg-emerald-500" },
  { status: "rejected", label: "Rejected", accent: "bg-zinc-400" },
];

export default function ManageCastingCallPage() {
  const params = useParams<{ id: string }>();
  const { token } = useAuth();
  const [call, setCall] = useState<CastingCall | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api.getCastingCall(params.id).then(setCall).catch(() => {});
    api
      .listApplicationsForCastingCall(params.id, token)
      .then(setApplications)
      .catch(() => setError("Could not load applications for this casting call."));
    api.listInvitationsForCastingCall(params.id, token).then(setInvitations).catch(() => {});
  }, [params.id, token]);

  async function handleStatusChange(applicationId: string, status: ApplicationStatus) {
    if (!token) return;
    setUpdatingId(applicationId);
    try {
      const updated = await api.updateApplicationStatus(applicationId, status, token);
      setApplications((prev) => prev.map((a) => (a.id === applicationId ? updated : a)));
    } catch {
      setError("Could not update that application.");
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">
      <Link href="/dashboard" className="text-sm font-semibold text-rose-600 hover:underline">
        ← Back to dashboard
      </Link>
      <h1 className="mt-4 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
        {call?.title ?? "Casting call"}
      </h1>
      <p className="mt-1 text-sm text-zinc-500">
        {applications.length} application{applications.length === 1 ? "" : "s"}
      </p>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {applications.length === 0 ? (
        <div className="mt-8 rounded-xl border-2 border-dashed border-zinc-200 p-8 text-center dark:border-zinc-800">
          <p className="text-sm text-zinc-500">No applications yet.</p>
        </div>
      ) : (
        <div className="mt-8 grid grid-cols-1 gap-4 overflow-x-auto sm:grid-cols-2 lg:grid-cols-4">
          {COLUMNS.map((column) => {
            const columnApplications = applications.filter((a) => a.status === column.status);
            return (
              <div key={column.status} className="flex min-w-[15rem] flex-col gap-3">
                <div className="flex items-center gap-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${column.accent}`} />
                  <span className={eyebrowClass}>
                    {column.label} · {columnApplications.length}
                  </span>
                </div>
                <div className="flex flex-col gap-3">
                  {columnApplications.map((a) => (
                    <ApplicationCard
                      key={a.id}
                      application={a}
                      roleTitle={call?.roles.find((r) => r.id === a.role_id)?.title}
                      updating={updatingId === a.id}
                      onMove={(status) => handleStatusChange(a.id, status)}
                    />
                  ))}
                  {columnApplications.length === 0 && (
                    <div className="rounded-2xl border-2 border-dashed border-zinc-200 p-4 text-center text-xs text-zinc-400 dark:border-zinc-800">
                      Nothing here
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {invitations.length > 0 && (
        <div className="mt-10">
          <span className={eyebrowClass}>Invitations sent · {invitations.length}</span>
          <ul className="mt-3 flex flex-col gap-2">
            {invitations.map((inv) => (
              <li
                key={inv.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border-2 border-zinc-100 p-3 text-sm dark:border-zinc-800"
              >
                <Link href={`/talents/${inv.talent_id}`} className="font-semibold text-rose-600 hover:underline">
                  View talent profile
                </Link>
                <span className={badgeClass(invitationStatusTone(inv.status))}>{inv.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}

function ApplicationCard({
  application,
  roleTitle,
  updating,
  onMove,
}: {
  application: Application;
  roleTitle?: string;
  updating: boolean;
  onMove: (status: ApplicationStatus) => void;
}) {
  const otherStatuses = COLUMNS.map((c) => c.status).filter((s) => s !== application.status);

  return (
    <div className="rounded-2xl border-2 border-zinc-100 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      {roleTitle && (
        <p className="mb-1 text-[11px] font-bold uppercase tracking-wide text-zinc-400">Applied for: {roleTitle}</p>
      )}
      <Link href={`/talents/${application.talent_id}`} className="text-sm font-semibold text-rose-600 hover:underline">
        View talent profile
      </Link>
      {application.submission_url && (
        <a
          href={application.submission_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-1 flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:underline dark:text-emerald-400"
        >
          <Play className="h-3 w-3" fill="currentColor" strokeWidth={0} /> View their submission
        </a>
      )}
      {application.message && (
        <p className="mt-2 line-clamp-3 text-xs text-zinc-600 dark:text-zinc-400">{application.message}</p>
      )}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {otherStatuses.map((s) => (
          <button
            key={s}
            disabled={updating}
            onClick={() => onMove(s)}
            className="rounded-md border-2 border-zinc-200 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-zinc-600 transition-colors hover:border-rose-300 hover:bg-rose-50 hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-rose-950 dark:hover:text-rose-300"
          >
            → {s}
          </button>
        ))}
      </div>
    </div>
  );
}

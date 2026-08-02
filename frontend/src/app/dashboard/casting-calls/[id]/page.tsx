"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ApiError,
  Application,
  ApplicationStatus,
  CastingCall,
  Invitation,
  TALENT_CATEGORIES,
  TalentCategory,
  api,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnPrimary, btnSecondary, eyebrowClass, formatCategory, inputClass, invitationStatusTone, labelClass } from "@/lib/ui";
import SubmissionPreview from "@/components/SubmissionPreview";

function parseTags(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

const COLUMNS: { status: ApplicationStatus; label: string; accent: string }[] = [
  { status: "pending", label: "Pending review", accent: "bg-amber-500" },
  { status: "shortlisted", label: "Shortlisted", accent: "bg-rose-500" },
  { status: "accepted", label: "Accepted", accent: "bg-emerald-500" },
  { status: "rejected", label: "Rejected", accent: "bg-zinc-400" },
];

export default function ManageCastingCallPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { token } = useAuth();
  const [call, setCall] = useState<CastingCall | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

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

  async function handleDeleteCall() {
    if (!token || !call) return;
    if (!window.confirm("Delete this talent hunt? Its applications and invitations will be removed too.")) return;
    setDeleting(true);
    try {
      await api.deleteCastingCall(call.id, token);
      router.push("/dashboard");
    } catch {
      setError("Could not delete this talent hunt.");
      setDeleting(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">
      <Link href="/dashboard" className="text-sm font-semibold text-rose-600 hover:underline">
        ← Back to dashboard
      </Link>
      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
            {call?.title ?? "Casting call"}
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            {applications.length} application{applications.length === 1 ? "" : "s"}
          </p>
        </div>
        {call && (
          <div className="flex items-center gap-3">
            <button type="button" onClick={() => setEditing((e) => !e)} className={btnSecondary}>
              {editing ? "Cancel edit" : "Edit posting"}
            </button>
            <button
              type="button"
              disabled={deleting}
              onClick={handleDeleteCall}
              className="rounded-full border-2 border-red-200 px-4 py-2 text-sm font-bold text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50 dark:border-red-900 dark:hover:bg-red-950"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {editing && call && (
        <EditCastingCallForm
          call={call}
          token={token!}
          onSaved={(updated) => {
            setCall(updated);
            setEditing(false);
          }}
        />
      )}

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
      {application.submission_url && <SubmissionPreview url={application.submission_url} />}
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

function EditCastingCallForm({
  call,
  token,
  onSaved,
}: {
  call: CastingCall;
  token: string;
  onSaved: (call: CastingCall) => void;
}) {
  const [title, setTitle] = useState(call.title);
  const [description, setDescription] = useState(call.description);
  const [category, setCategory] = useState<TalentCategory>(call.category);
  const [location, setLocation] = useState(call.location ?? "");
  const [compensation, setCompensation] = useState(call.compensation ?? "");
  const [applicationDeadline, setApplicationDeadline] = useState(call.application_deadline ?? "");
  const [auditionBrief, setAuditionBrief] = useState(call.audition_brief ?? "");
  const [auditionReferenceUrl, setAuditionReferenceUrl] = useState(call.audition_reference_url ?? "");
  const [tagsInput, setTagsInput] = useState((call.tags ?? []).join(", "));
  const [shootDetails, setShootDetails] = useState(call.shoot_details ?? "");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const updated = await api.updateCastingCall(
        call.id,
        {
          title,
          description,
          category,
          location: location || undefined,
          compensation: compensation || undefined,
          application_deadline: applicationDeadline || undefined,
          audition_brief: auditionBrief || undefined,
          audition_reference_url: auditionReferenceUrl || undefined,
          tags: parseTags(tagsInput),
          shoot_details: shootDetails || undefined,
        },
        token
      );
      onSaved(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save these changes.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-6 flex flex-col gap-4 rounded-2xl border-2 border-zinc-100 p-5 dark:border-zinc-800"
    >
      <label className={labelClass}>
        Title
        <input required value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} />
      </label>
      <label className={labelClass}>
        Category
        <select value={category} onChange={(e) => setCategory(e.target.value as TalentCategory)} className={inputClass}>
          {TALENT_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {formatCategory(c)}
            </option>
          ))}
        </select>
      </label>
      <label className={labelClass}>
        Description
        <textarea
          required
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={inputClass}
        />
      </label>
      <label className={labelClass}>
        Location
        <input value={location} onChange={(e) => setLocation(e.target.value)} className={inputClass} />
      </label>
      <label className={labelClass}>
        Compensation
        <input value={compensation} onChange={(e) => setCompensation(e.target.value)} className={inputClass} />
      </label>
      <label className={labelClass}>
        Application deadline
        <input
          type="date"
          value={applicationDeadline}
          onChange={(e) => setApplicationDeadline(e.target.value)}
          className={inputClass}
        />
      </label>
      <label className={labelClass}>
        Audition brief
        <textarea
          rows={3}
          value={auditionBrief}
          onChange={(e) => setAuditionBrief(e.target.value)}
          className={inputClass}
        />
      </label>
      <label className={labelClass}>
        Audition reference URL
        <input
          value={auditionReferenceUrl}
          onChange={(e) => setAuditionReferenceUrl(e.target.value)}
          className={inputClass}
        />
      </label>
      <label className={labelClass}>
        Tags (comma separated)
        <input value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} className={inputClass} />
      </label>
      <label className={labelClass}>
        Shoot details
        <textarea
          rows={3}
          value={shootDetails}
          onChange={(e) => setShootDetails(e.target.value)}
          className={inputClass}
        />
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button type="submit" disabled={submitting} className={btnPrimary}>
        {submitting ? "Saving…" : "Save changes"}
      </button>
    </form>
  );
}

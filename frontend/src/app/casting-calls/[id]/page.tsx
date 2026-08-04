"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Check, Clapperboard, Paperclip, Star } from "lucide-react";
import { ApiError, CastingCall, CastingCallRole, RecruiterProfile, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import CategoryIcon from "@/components/CategoryIcon";
import FollowRecruiterButton from "@/components/FollowRecruiterButton";
import ReportButton from "@/components/ReportButton";
import {
  badgeClass,
  btnPrimary,
  btnSmall,
  categoryBadgeClass,
  formatCategory,
  inputClass,
  labelClass,
  sectionClass,
  statusTone,
} from "@/lib/ui";

export default function CastingCallDetailPage() {
  return (
    <Suspense fallback={null}>
      <CastingCallDetailContent />
    </Suspense>
  );
}

function CastingCallDetailContent() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const { user, token } = useAuth();

  const [call, setCall] = useState<CastingCall | null>(null);
  const [recruiter, setRecruiter] = useState<RecruiterProfile | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedRoleId, setSelectedRoleId] = useState(searchParams.get("role") ?? "");
  const [message, setMessage] = useState("");
  const [submissionMode, setSubmissionMode] = useState<"upload" | "link">("upload");
  const [submissionUrl, setSubmissionUrl] = useState("");
  const [submissionFile, setSubmissionFile] = useState<File | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applied, setApplied] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [talentTier, setTalentTier] = useState<"free" | "premium" | null>(null);

  useEffect(() => {
    api
      .getCastingCall(params.id)
      .then((c) => {
        setCall(c);
        setSelectedRoleId((prev) => prev || c.roles[0]?.id || "");
        api.getRecruiter(c.recruiter_id).then(setRecruiter).catch(() => {});
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Could not load this casting call."));
    api.trackCastingCallView(params.id).catch(() => {});
  }, [params.id]);

  useEffect(() => {
    if (!token || user?.role !== "talent") return;
    api.getMyTalentProfile(token).then((p) => setTalentTier(p.tier)).catch(() => {});
  }, [token, user]);

  async function handleApply(e: FormEvent) {
    e.preventDefault();
    if (!token || !selectedRoleId) return;
    setApplyError(null);
    setSubmitting(true);
    try {
      if (submissionMode === "upload" && submissionFile) {
        const mediaType = submissionFile.type.startsWith("audio/") ? "audio" : "video";
        await api.applyToCastingCallWithUpload(
          params.id,
          { role_id: selectedRoleId, media_type: mediaType, file: submissionFile, message: message || undefined },
          token
        );
      } else {
        await api.applyToCastingCall(
          params.id,
          { role_id: selectedRoleId, message: message || undefined, submission_url: submissionUrl || undefined },
          token
        );
      }
      setApplied(true);
    } catch (err) {
      setApplyError(err instanceof ApiError ? err.message : "Could not submit your application.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-14">
        <p className="text-sm text-red-600">{loadError}</p>
      </main>
    );
  }

  if (!call) {
    return (
      <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-14">
        <p className="text-sm text-zinc-500">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-14">
      <div className="flex flex-wrap items-center gap-2">
        {call.is_featured && (
          <span className="inline-flex items-center gap-1 rounded-sm bg-amber-400 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-zinc-900">
            <Star className="h-3 w-3" fill="currentColor" strokeWidth={0} /> Featured
          </span>
        )}
        {call.premium_talent_only && (
          <span className="inline-flex items-center gap-1 rounded-sm bg-zinc-900 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-white dark:bg-zinc-100 dark:text-zinc-900">
            Premium talent only
          </span>
        )}
        <span className={badgeClass(statusTone(call.status))}>{call.status}</span>
        {user?.role === "talent" && <FollowRecruiterButton recruiterId={call.recruiter_id} />}
        {user && <ReportButton targetType="casting_call" targetId={call.id} />}
      </div>

      <h1 className="mt-3 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
        {call.title}
      </h1>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className={categoryBadgeClass(call.category)}>{formatCategory(call.category)}</span>
        <span className="text-sm text-zinc-500">{call.location || "Worldwide"}</span>
        {recruiter && (
          <span className="text-sm text-zinc-500">
            · Posted by{" "}
            <Link href={`/recruiters/${recruiter.id}`} className="font-semibold text-rose-600 hover:underline">
              {recruiter.company_name}
            </Link>
          </span>
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-sm text-zinc-600 dark:text-zinc-400">
        {call.compensation && (
          <span className="rounded-full bg-emerald-100 px-3 py-1 font-semibold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
            {call.compensation}
          </span>
        )}
        {call.application_deadline && <span>Apply by {call.application_deadline}</span>}
      </div>

      {call.tags && call.tags.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {call.tags.map((t) => (
            <span
              key={t}
              className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-3 py-1 text-xs font-semibold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
            >
              <Check className="h-3 w-3" /> {t}
            </span>
          ))}
        </div>
      )}

      <p className="mt-6 whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">{call.description}</p>

      {call.audition_brief && (
        <div className="mt-6 rounded-xl border-2 border-rose-200 bg-rose-50 p-5 dark:border-rose-900 dark:bg-rose-950/20">
          <h2 className="flex items-center gap-2 font-heading text-lg font-black uppercase tracking-tight text-rose-900 dark:text-rose-200">
            <Clapperboard className="h-4 w-4" /> What to perform
          </h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-rose-800 dark:text-rose-300">{call.audition_brief}</p>
          {call.audition_reference_url && (
            <a
              href={call.audition_reference_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-rose-700 hover:underline dark:text-rose-300"
            >
              <Paperclip className="h-3.5 w-3.5" /> View reference material →
            </a>
          )}
        </div>
      )}

      {call.roles.length > 1 && (
        <div className="mt-8">
          <h2 className="font-heading text-lg font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
            Roles in this project
          </h2>
          <div className="mt-3 flex flex-col gap-3">
            {call.roles.map((role) => (
              <RoleCard
                key={role.id}
                role={role}
                fallbackCategory={call.category}
                selected={role.id === selectedRoleId}
                onApply={() => {
                  setSelectedRoleId(role.id);
                  document.getElementById("apply-section")?.scrollIntoView({ behavior: "smooth" });
                }}
              />
            ))}
          </div>
        </div>
      )}

      {call.shoot_details && (
        <div className="mt-8">
          <h2 className="font-heading text-lg font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
            Dates & Locations
          </h2>
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">{call.shoot_details}</p>
        </div>
      )}

      <div id="apply-section" className={`mt-10 ${sectionClass}`}>
        {call.status !== "open" ? (
          <p className="text-sm text-zinc-500">This casting call is closed.</p>
        ) : !user ? (
          <p className="text-sm text-zinc-500">
            <Link href="/login" className="font-semibold text-rose-600 hover:underline">
              Log in
            </Link>{" "}
            as talent to apply.
          </p>
        ) : user.role !== "talent" ? (
          <p className="text-sm text-zinc-500">Only talent accounts can apply to casting calls.</p>
        ) : call.premium_talent_only && talentTier !== "premium" ? (
          <p className="text-sm text-zinc-500">
            This talent hunt is open to Premium talent only.{" "}
            <Link href="/dashboard" className="font-semibold text-rose-600 hover:underline">
              Upgrade your account
            </Link>{" "}
            to apply.
          </p>
        ) : applied ? (
          <p className="flex items-center gap-1.5 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
            <Check className="h-4 w-4" /> Application submitted.
          </p>
        ) : (
          <form onSubmit={handleApply} className="flex flex-col gap-3">
            <h3 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">Ready to apply?</h3>
            {call.roles.length > 1 && (
              <label className={labelClass}>
                Role
                <select
                  value={selectedRoleId}
                  onChange={(e) => setSelectedRoleId(e.target.value)}
                  className={inputClass}
                >
                  {call.roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.title}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {call.audition_brief && (
              <div className="flex flex-col gap-2">
                <span className="text-xs font-bold uppercase tracking-wide text-zinc-500">Your performed take</span>
                <fieldset className="grid grid-cols-2 gap-2">
                  {(["upload", "link"] as const).map((mode) => (
                    <button
                      type="button"
                      key={mode}
                      onClick={() => setSubmissionMode(mode)}
                      className={`rounded-md border-2 px-3 py-2 text-sm font-medium capitalize transition-colors ${
                        submissionMode === mode
                          ? "border-rose-600 bg-rose-600 text-white"
                          : "border-zinc-200 text-zinc-700 hover:border-rose-300 hover:bg-rose-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-rose-800 dark:hover:bg-rose-950"
                      }`}
                    >
                      {mode === "upload" ? "Upload a file" : "Paste a link"}
                    </button>
                  ))}
                </fieldset>
                {submissionMode === "upload" ? (
                  <label key="submission-file" className={labelClass}>
                    Video or audio file
                    <input
                      type="file"
                      accept="video/*,audio/*"
                      onChange={(e) => setSubmissionFile(e.target.files?.[0] ?? null)}
                      className={inputClass}
                    />
                    <span className="mt-1 block text-xs font-normal normal-case text-zinc-500">
                      We&apos;ll compress it automatically.
                    </span>
                  </label>
                ) : (
                  <label key="submission-url" className={labelClass}>
                    URL
                    <input
                      type="url"
                      value={submissionUrl}
                      onChange={(e) => setSubmissionUrl(e.target.value)}
                      placeholder="https://… (YouTube, Spotify, or wherever you've hosted it)"
                      className={inputClass}
                    />
                  </label>
                )}
              </div>
            )}
            <label className={labelClass}>
              Message to the recruiter (optional)
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                className={inputClass}
              />
            </label>
            {applyError && <p className="text-sm text-red-600">{applyError}</p>}
            <button type="submit" disabled={submitting} className={`${btnPrimary} w-fit`}>
              {submitting ? "Submitting…" : "Apply"}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}

function RoleCard({
  role,
  fallbackCategory,
  selected,
  onApply,
}: {
  role: CastingCallRole;
  fallbackCategory: string;
  selected: boolean;
  onApply: () => void;
}) {
  return (
    <div
      className={`flex items-start justify-between gap-4 rounded-xl border-2 p-4 ${
        selected ? "border-rose-400 bg-rose-50 dark:bg-rose-950/20" : "border-zinc-200 dark:border-zinc-800"
      }`}
    >
      <div>
        <p className="flex items-center gap-1.5 font-heading text-base font-bold text-zinc-900 dark:text-zinc-50">
          <CategoryIcon category={role.category ?? fallbackCategory} className="h-4 w-4 text-zinc-500" />
          {role.title}
        </p>
        {role.criteria && <p className="mt-1 text-sm text-zinc-500">{role.criteria}</p>}
        {role.compensation && (
          <p className="mt-1 text-sm font-semibold text-emerald-700 dark:text-emerald-400">{role.compensation}</p>
        )}
      </div>
      <button onClick={onApply} className={selected ? `${btnSmall} !border-rose-500 !text-rose-600` : btnSmall}>
        {selected ? (
          <>
            <Check className="h-3.5 w-3.5" /> Selected
          </>
        ) : (
          "Apply"
        )}
      </button>
    </div>
  );
}

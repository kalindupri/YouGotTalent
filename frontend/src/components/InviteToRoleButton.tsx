"use client";

import { useState } from "react";
import { Check, Mail } from "lucide-react";
import { ApiError, CastingCall, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnSmall, btnSmallPrimary, formatCategory, inputClass, labelClass } from "@/lib/ui";

export default function InviteToRoleButton({ talentId }: { talentId: string }) {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [calls, setCalls] = useState<CastingCall[]>([]);
  const [castingCallId, setCastingCallId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleOpen() {
    setOpen(true);
    if (calls.length > 0 || !token) return;
    setLoading(true);
    try {
      const recruiter = await api.getMyRecruiterProfile(token);
      const all = await api.listCastingCalls();
      const mine = all.filter((c) => c.recruiter_id === recruiter.id && c.status === "open");
      setCalls(mine);
      if (mine.length > 0) setCastingCallId(mine[0].id);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (!token || !castingCallId) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.inviteTalentToCastingCall(castingCallId, { talent_id: talentId, message: message || undefined }, token);
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send this invitation.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative">
      <button onClick={handleOpen} className={btnSmall}>
        <Mail className="h-3.5 w-3.5" /> Invite to a role
      </button>

      {open && (
        <div className="absolute right-0 top-full z-10 mt-2 w-72 rounded-xl border border-zinc-200 bg-white p-4 shadow-lg dark:border-zinc-800 dark:bg-zinc-900">
          {sent ? (
            <p className="flex items-center gap-1.5 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
              <Check className="h-4 w-4" /> Invitation sent — they&apos;ll see it on their dashboard.
            </p>
          ) : loading ? (
            <p className="text-sm text-zinc-500">Loading your talent hunts…</p>
          ) : calls.length === 0 ? (
            <p className="text-sm text-zinc-500">
              You don&apos;t have any open talent hunts to invite them to yet.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              <label className={labelClass}>
                Invite to
                <select
                  value={castingCallId}
                  onChange={(e) => setCastingCallId(e.target.value)}
                  className={inputClass}
                >
                  {calls.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title} · {formatCategory(c.category)}
                    </option>
                  ))}
                </select>
              </label>
              <label className={labelClass}>
                Message (optional)
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={3}
                  className={inputClass}
                />
              </label>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setOpen(false)} className={btnSmall}>
                  Cancel
                </button>
                <button type="button" onClick={handleSubmit} disabled={submitting} className={btnSmallPrimary}>
                  {submitting ? "Sending…" : "Send invite"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

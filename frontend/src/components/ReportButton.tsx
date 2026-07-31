"use client";

import { useState } from "react";
import { Check, Flag } from "lucide-react";
import { ApiError, ReportCategory, ReportTargetType, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnSmall, btnSmallPrimary, inputClass, labelClass } from "@/lib/ui";

const CATEGORY_OPTIONS: { value: ReportCategory; label: string }[] = [
  { value: "spam", label: "Spam" },
  { value: "harassment", label: "Harassment or abuse" },
  { value: "fake_profile", label: "Fake or impersonating profile" },
  { value: "inappropriate_content", label: "Inappropriate content" },
  { value: "other", label: "Other" },
];

interface ReportButtonProps {
  targetType: ReportTargetType;
  targetId: string;
  label?: string;
}

export default function ReportButton({ targetType, targetId, label = "Report" }: ReportButtonProps) {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<ReportCategory>("spam");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  if (!token) return null;

  async function handleSubmit() {
    if (!token || !description.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.submitReport(
        {
          category,
          target_type: targetType,
          target_id: targetId,
          subject: CATEGORY_OPTIONS.find((c) => c.value === category)?.label ?? category,
          description: description.trim(),
          page_url: typeof window !== "undefined" ? window.location.href : undefined,
        },
        token
      );
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit this report.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleClose() {
    setOpen(false);
    setSent(false);
    setDescription("");
    setError(null);
  }

  return (
    <div className="relative">
      <button onClick={() => setOpen(true)} className={`${btnSmall} !text-zinc-500`}>
        <Flag className="h-3.5 w-3.5" /> {label}
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={handleClose}>
          <div
            className="w-full max-w-sm rounded-xl border border-zinc-200 bg-white p-5 shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
            onClick={(e) => e.stopPropagation()}
          >
            {sent ? (
              <p className="flex items-center gap-1.5 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                <Check className="h-4 w-4" /> Thanks — our team will review this.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                <h3 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">Report</h3>
                <label className={labelClass}>
                  Reason
                  <select value={category} onChange={(e) => setCategory(e.target.value as ReportCategory)} className={inputClass}>
                    {CATEGORY_OPTIONS.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className={labelClass}>
                  Details
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={4}
                    placeholder="What happened?"
                    className={inputClass}
                  />
                </label>
                {error && <p className="text-sm text-red-600">{error}</p>}
                <div className="flex justify-end gap-2">
                  <button type="button" onClick={handleClose} className={btnSmall}>
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={submitting || !description.trim()}
                    className={btnSmallPrimary}
                  >
                    {submitting ? "Sending…" : "Submit report"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

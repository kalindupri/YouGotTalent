"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import { ApiError, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnSmall, btnSmallPrimary, inputClass, labelClass } from "@/lib/ui";

export default function ReportBugLink() {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  if (!token) return null;

  async function handleSubmit() {
    if (!token || !subject.trim() || !description.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.submitReport(
        {
          category: "bug",
          subject: subject.trim(),
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
    setSubject("");
    setDescription("");
    setError(null);
  }

  return (
    <>
      <button onClick={() => setOpen(true)} className="hover:text-rose-500">
        Report a problem
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={handleClose}>
          <div
            className="w-full max-w-sm rounded-xl border border-zinc-200 bg-white p-5 shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
            onClick={(e) => e.stopPropagation()}
          >
            {sent ? (
              <p className="flex items-center gap-1.5 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                <Check className="h-4 w-4" /> Thanks for the report — we&apos;ll look into it.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                <h3 className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">Report a problem</h3>
                <label className={labelClass}>
                  Summary
                  <input
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="e.g. Upload button doesn't work"
                    className={inputClass}
                  />
                </label>
                <label className={labelClass}>
                  What happened?
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={4}
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
                    disabled={submitting || !subject.trim() || !description.trim()}
                    className={btnSmallPrimary}
                  >
                    {submitting ? "Sending…" : "Submit"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

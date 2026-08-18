"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, FileText, X } from "lucide-react";
import { AdminGuardianConsent, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnSmall, btnSmallPrimary, inputClass, labelClass, sectionClass } from "@/lib/ui";
import Modal from "@/components/Modal";

const RELATIONSHIP_LABELS: Record<string, string> = {
  mother: "Mother",
  father: "Father",
  legal_guardian: "Legal guardian",
};

const DOC_LABELS: Record<string, string> = {
  birth_certificate: "Birth certificate",
  guardian_id: "Guardian ID",
  guardianship_order: "Guardianship order",
};

export default function GuardianConsentQueue() {
  const { token } = useAuth();
  const [consents, setConsents] = useState<AdminGuardianConsent[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState<AdminGuardianConsent | null>(null);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!token) return;
    api
      .adminListGuardianConsents(token)
      .then(setConsents)
      .catch(() => {});
  }, [token]);

  useEffect(refresh, [refresh]);

  async function handleApprove(consent: AdminGuardianConsent) {
    if (!token) return;
    setBusyId(consent.id);
    try {
      await api.adminApproveGuardianConsent(consent.id, token);
      setConsents((prev) => prev.filter((c) => c.id !== consent.id));
    } finally {
      setBusyId(null);
    }
  }

  async function handleReject() {
    if (!token || !rejecting) return;
    setBusyId(rejecting.id);
    setError(null);
    try {
      await api.adminRejectGuardianConsent(rejecting.id, reason, token);
      setConsents((prev) => prev.filter((c) => c.id !== rejecting.id));
      setRejecting(null);
      setReason("");
    } catch {
      setError("Give a reason of at least 10 characters — the guardian is told why.");
    } finally {
      setBusyId(null);
    }
  }

  async function openDocument(consentId: string, documentId: string) {
    if (!token) return;
    // The link is minted on demand and expires in minutes, so it isn't left sitting in the
    // page or in browser history.
    const { url } = await api.adminGuardianConsentDocumentLink(consentId, documentId, token);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Guardian consent</h2>
      <p className="mt-1 text-sm text-zinc-500">
        Profiles belonging to under-18s stay hidden from talent hunts until a parent or legal guardian&apos;s
        consent is approved here. Check the uploaded documents actually prove the relationship.
      </p>

      {consents.length === 0 ? (
        <p className="mt-4 text-sm text-zinc-500">No consent requests waiting for review.</p>
      ) : (
        <ul className="mt-4 flex flex-col gap-3">
          {consents.map((consent) => (
            <li key={consent.id} className="rounded-2xl border-2 border-zinc-100 p-4 dark:border-zinc-800">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-semibold text-zinc-900 dark:text-zinc-50">
                    {consent.talent_display_name ?? consent.minor_full_name}
                    {consent.minor_age !== null && (
                      <span className={`ml-2 ${badgeClass}`}>Age {consent.minor_age}</span>
                    )}
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">
                    Legal name: {consent.minor_full_name} · born {consent.minor_date_of_birth}
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">
                    Guardian: {consent.guardian_full_name} (
                    {RELATIONSHIP_LABELS[consent.guardian_relationship] ?? consent.guardian_relationship})
                    {consent.guardian_email ? ` · ${consent.guardian_email}` : ""}
                    {consent.guardian_phone ? ` · ${consent.guardian_phone}` : ""}
                  </p>
                  {consent.consented_scopes && (
                    <p className="mt-1 text-xs text-zinc-500">Consented to: {consent.consented_scopes.join(", ")}</p>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <button
                    onClick={() => handleApprove(consent)}
                    disabled={busyId === consent.id}
                    className={btnSmallPrimary}
                  >
                    <Check className="h-3.5 w-3.5" /> Approve
                  </button>
                  <button
                    onClick={() => {
                      setRejecting(consent);
                      setReason("");
                      setError(null);
                    }}
                    disabled={busyId === consent.id}
                    className={btnSmall}
                  >
                    <X className="h-3.5 w-3.5" /> Reject
                  </button>
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                {consent.documents.map((doc) => (
                  <button key={doc.id} onClick={() => openDocument(consent.id, doc.id)} className={btnSmall}>
                    <FileText className="h-3.5 w-3.5" /> {DOC_LABELS[doc.doc_type] ?? doc.doc_type}
                  </button>
                ))}
                {consent.documents.length === 0 && (
                  <span className="text-xs text-zinc-400">No documents attached.</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {rejecting !== null && (
        <Modal onClose={() => setRejecting(null)} title="Reject guardian consent">
          <div className="flex flex-col gap-3">
          <label className={labelClass}>
            Why are you rejecting this?
            <textarea
              rows={4}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. The birth certificate is unreadable — please upload a clearer scan."
              className={inputClass}
            />
            <span className="mt-1 block text-xs font-normal text-zinc-500">
              This is sent to the guardian, so write it as something they can act on.
            </span>
          </label>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex items-center gap-3">
              <button onClick={handleReject} disabled={busyId !== null} className={btnSmallPrimary}>
                Reject and notify
              </button>
              <button onClick={() => setRejecting(null)} className={btnSmall}>
                Cancel
              </button>
            </div>
          </div>
        </Modal>
      )}
    </section>
  );
}

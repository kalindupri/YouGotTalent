"use client";

import { FormEvent, useState } from "react";
import { FileCheck2 } from "lucide-react";
import { ApiError, Booking, api } from "@/lib/api";
import { btnPrimary, btnSmall, inputClass, labelClass } from "@/lib/ui";
import Modal from "@/components/Modal";
import AgreementDocument from "@/components/AgreementDocument";

function formatSignedAt(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function BookingAgreementSection({
  booking,
  token,
  viewerRole,
  otherPartyLabel,
  onUpdated,
}: {
  booking: Booking;
  token: string;
  viewerRole: "talent" | "recruiter";
  otherPartyLabel: string;
  onUpdated: (updated: Booking) => void;
}) {
  const [signatureName, setSignatureName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewing, setViewing] = useState(false);

  const hasContract = !!booking.contract_content;
  const mySignedAt = viewerRole === "talent" ? booking.talent_signed_at : booking.recruiter_signed_at;
  const mySignatureName = viewerRole === "talent" ? booking.talent_signature_name : booking.recruiter_signature_name;
  const theirSignedAt = viewerRole === "talent" ? booking.recruiter_signed_at : booking.talent_signed_at;
  const theirSignatureName = viewerRole === "talent" ? booking.recruiter_signature_name : booking.talent_signature_name;

  async function handleSign(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const updated = await api.signBookingAgreement(booking.id, signatureName, token);
      onUpdated(updated);
      setViewing(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not sign this agreement.");
    } finally {
      setSubmitting(false);
    }
  }

  const signForm = (
    <form onSubmit={handleSign} className="mt-3 flex flex-wrap items-end gap-2 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
      <label className={labelClass}>
        Type your full name to sign
        <input
          value={signatureName}
          onChange={(e) => setSignatureName(e.target.value)}
          placeholder="Full legal name"
          required
          className={inputClass}
        />
      </label>
      <button type="submit" disabled={submitting || !signatureName.trim()} className={btnSmall}>
        <FileCheck2 className="h-3.5 w-3.5" /> {submitting ? "Signing…" : "Sign agreement"}
      </button>
      {theirSignedAt && (
        <p className="w-full text-xs text-zinc-400">
          {theirSignatureName} ({otherPartyLabel}) already signed on {formatSignedAt(theirSignedAt)}.
        </p>
      )}
      {error && <p className="w-full text-xs text-red-600">{error}</p>}
    </form>
  );

  const viewAgreementButton = hasContract && (
    <button type="button" onClick={() => setViewing(true)} className={`${btnSmall} mt-2`}>
      View agreement
    </button>
  );

  if (booking.agreement_status === "signed") {
    return (
      <div className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm dark:bg-emerald-950/40">
        <p className="flex items-center gap-1.5 font-semibold text-emerald-700 dark:text-emerald-400">
          <FileCheck2 className="h-4 w-4" /> Agreement signed by both parties
        </p>
        <ul className="mt-2 flex flex-col gap-0.5 text-zinc-600 dark:text-zinc-400">
          {booking.talent_signature_name && booking.talent_signed_at && (
            <li>
              {booking.talent_signature_name} (talent) &mdash; {formatSignedAt(booking.talent_signed_at)}
            </li>
          )}
          {booking.recruiter_signature_name && booking.recruiter_signed_at && (
            <li>
              {booking.recruiter_signature_name} (talent hunt) &mdash; {formatSignedAt(booking.recruiter_signed_at)}
            </li>
          )}
        </ul>
        {viewAgreementButton}
        {viewing && (
          <Modal title="Signed agreement" onClose={() => setViewing(false)}>
            <AgreementDocument booking={booking} />
          </Modal>
        )}
      </div>
    );
  }

  if (mySignedAt) {
    return (
      <div className="mt-3 rounded-lg bg-zinc-50 p-3 text-sm dark:bg-zinc-800/60">
        <p className="text-zinc-700 dark:text-zinc-300">
          You signed as <span className="font-semibold">{mySignatureName}</span> on {formatSignedAt(mySignedAt)}.
        </p>
        <p className="mt-1 text-zinc-500">Waiting for {otherPartyLabel} to sign.</p>
        {viewAgreementButton}
        {viewing && (
          <Modal title="Agreement" onClose={() => setViewing(false)}>
            <AgreementDocument booking={booking} />
          </Modal>
        )}
      </div>
    );
  }

  if (!hasContract) {
    return signForm;
  }

  return (
    <div className="mt-3">
      <button type="button" onClick={() => setViewing(true)} className={btnPrimary}>
        <FileCheck2 className="h-3.5 w-3.5" /> View &amp; sign agreement
      </button>
      {theirSignedAt && (
        <p className="mt-1 text-xs text-zinc-400">
          {theirSignatureName} ({otherPartyLabel}) already signed on {formatSignedAt(theirSignedAt)}.
        </p>
      )}
      {viewing && (
        <Modal title="Review & sign agreement" onClose={() => setViewing(false)}>
          <AgreementDocument booking={booking} />
          {signForm}
        </Modal>
      )}
    </div>
  );
}

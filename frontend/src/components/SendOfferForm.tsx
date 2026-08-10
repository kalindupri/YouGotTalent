"use client";

import { FormEvent, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { btnPrimary, btnSmall, defaultContractTemplate } from "@/lib/ui";
import Modal from "@/components/Modal";
import RichTextEditor from "@/components/RichTextEditor";

export default function SendOfferForm({
  talentId,
  applicationId,
  talentDisplayName,
  companyName,
  roleTitle,
  token,
  onSent,
  onCancel,
}: {
  talentId: string;
  applicationId: string;
  talentDisplayName: string;
  companyName: string;
  roleTitle?: string;
  token: string;
  onSent: () => void;
  onCancel: () => void;
}) {
  const [contractContent, setContractContent] = useState(() =>
    defaultContractTemplate({ companyName, talentName: talentDisplayName, roleTitle })
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.requestBooking(talentId, { application_id: applicationId, contract_content: contractContent }, token);
      onSent();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not send this offer.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal title={`Draft contract offer for ${talentDisplayName}`} onClose={onCancel}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <p className="text-xs text-zinc-500">
          Edit this branded agreement, then send it — no date or time is needed. The talent reviews and signs it
          from their dashboard, and once you both sign, the application is automatically accepted.
        </p>
        <RichTextEditor value={contractContent} onChange={setContractContent} />
        {error && <p className="text-xs text-red-600">{error}</p>}
        <div className="flex gap-2">
          <button type="submit" disabled={submitting} className={btnPrimary}>
            {submitting ? "Sending…" : "Send offer"}
          </button>
          <button type="button" onClick={onCancel} className={btnSmall}>
            Cancel
          </button>
        </div>
      </form>
    </Modal>
  );
}

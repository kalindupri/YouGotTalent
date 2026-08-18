"use client";

import { FormEvent, useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import { ApiError, GuardianConsent, MyTalentProfile } from "@/lib/api";
import { btnPrimary, inputClass, labelClass, sectionClass } from "@/lib/ui";

const RELATIONSHIPS = [
  { value: "mother", label: "Mother" },
  { value: "father", label: "Father" },
  { value: "legal_guardian", label: "Legal guardian" },
];

const SCOPES = [
  { value: "profile_public", label: "Show their profile to talent hunts" },
  { value: "media_public", label: "Show their photos and audition media" },
  { value: "recruiter_contact", label: "Let talent hunts contact us about them" },
  { value: "paid_engagement", label: "Consider them for paid work (16+ only)" },
];

const CONSENT_STATEMENT =
  "I confirm I am the parent or legal guardian of the young person named above, that the documents " +
  "I have uploaded prove that relationship, and that I consent to YouGotTalent processing their " +
  "personal data — including their photographs and audition media — for the purposes I have selected, " +
  "in line with the Personal Data Protection Act No. 9 of 2022. I understand I can withdraw this " +
  "consent at any time.";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function GuardianConsentCard({
  profile,
  token,
  onSubmitted,
}: {
  profile: MyTalentProfile;
  token: string;
  onSubmitted: () => void;
}) {
  const [consent, setConsent] = useState<GuardianConsent | null>(null);
  const [guardianName, setGuardianName] = useState("");
  const [relationship, setRelationship] = useState("mother");
  const [minorName, setMinorName] = useState("");
  const [guardianEmail, setGuardianEmail] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [scopes, setScopes] = useState<string[]>(["profile_public", "recruiter_contact"]);
  const [agreed, setAgreed] = useState(false);
  const [birthCertificate, setBirthCertificate] = useState<File | null>(null);
  const [guardianId, setGuardianId] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/talents/me/guardian-consent`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : null))
      .then(setConsent)
      .catch(() => {});
  }, [token]);

  // Adults never see this card.
  if (profile.guardian_consent_status === "not_required") return null;

  function toggleScope(value: string) {
    setScopes((prev) => (prev.includes(value) ? prev.filter((s) => s !== value) : [...prev, value]));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!birthCertificate) {
      setError("Upload the young person's birth certificate.");
      return;
    }
    setSubmitting(true);
    try {
      const form = new FormData();
      form.append("guardian_full_name", guardianName);
      form.append("guardian_relationship", relationship);
      form.append("minor_full_name", minorName);
      if (guardianEmail) form.append("guardian_email", guardianEmail);
      if (guardianPhone) form.append("guardian_phone", guardianPhone);
      scopes.forEach((s) => form.append("consented_scopes", s));
      form.append("agreed", "true");
      form.append("birth_certificate", birthCertificate);
      if (guardianId) form.append("guardian_id", guardianId);

      const resp = await fetch(`${API_URL}/talents/me/guardian-consent`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (!resp.ok) {
        const detail = await resp.json().catch(() => null);
        throw new ApiError(resp.status, detail?.detail ?? "Could not submit consent.");
      }
      setConsent(await resp.json());
      onSubmitted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit consent.");
    } finally {
      setSubmitting(false);
    }
  }

  const status = profile.guardian_consent_status;

  return (
    <section className={sectionClass}>
      <div className="flex items-start gap-2">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-rose-600" />
        <div>
          <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Guardian consent</h2>
          <p className="mt-1 text-sm text-zinc-500">
            This profile belongs to someone under 18. Sri Lanka&apos;s Personal Data Protection Act treats a
            child&apos;s data as a special category, so a parent or legal guardian has to consent before the
            profile is visible to talent hunts.
          </p>
        </div>
      </div>

      {status === "submitted" && (
        <p className="mt-4 rounded-2xl bg-amber-50 p-4 text-sm text-amber-900 dark:bg-amber-900/20 dark:text-amber-200">
          Your consent is with our team for review. We&apos;ll email you as soon as it&apos;s approved — the
          profile stays hidden from talent hunts until then.
        </p>
      )}

      {status === "approved" && (
        <p className="mt-4 rounded-2xl bg-emerald-50 p-4 text-sm text-emerald-900 dark:bg-emerald-900/20 dark:text-emerald-200">
          Consent approved. The profile is live and talent hunts can find it.
        </p>
      )}

      {status === "rejected" && consent?.decision_reason && (
        <div className="mt-4 rounded-2xl bg-red-50 p-4 text-sm text-red-900 dark:bg-red-900/20 dark:text-red-200">
          <p className="font-semibold">We couldn&apos;t approve this yet</p>
          <p className="mt-1">{consent.decision_reason}</p>
          <p className="mt-1">Correct it below and submit again.</p>
        </div>
      )}

      {(status === "required" || status === "rejected" || status === "revoked") && (
        <form onSubmit={handleSubmit} className="mt-5 flex max-w-md flex-col gap-4">
          <label className={labelClass}>
            Your full legal name
            <input required value={guardianName} onChange={(e) => setGuardianName(e.target.value)} className={inputClass} />
          </label>
          <label className={labelClass}>
            Your relationship to them
            <select value={relationship} onChange={(e) => setRelationship(e.target.value)} className={inputClass}>
              {RELATIONSHIPS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          <label className={labelClass}>
            Their full legal name
            <input required value={minorName} onChange={(e) => setMinorName(e.target.value)} className={inputClass} />
            <span className="mt-1 block text-xs font-normal text-zinc-500">
              As it appears on the birth certificate — it can differ from their stage name on the profile.
            </span>
          </label>
          <label className={labelClass}>
            Your email (optional)
            <input type="email" value={guardianEmail} onChange={(e) => setGuardianEmail(e.target.value)} className={inputClass} />
          </label>
          <label className={labelClass}>
            Your phone (optional)
            <input value={guardianPhone} onChange={(e) => setGuardianPhone(e.target.value)} className={inputClass} />
          </label>

          <fieldset className="flex flex-col gap-1.5">
            <legend className={labelClass}>What are you consenting to?</legend>
            {SCOPES.map((s) => (
              <label key={s.value} className="flex items-start gap-2 text-sm text-zinc-700 dark:text-zinc-300">
                <input
                  type="checkbox"
                  checked={scopes.includes(s.value)}
                  onChange={() => toggleScope(s.value)}
                  className="mt-0.5 shrink-0 accent-rose-600"
                />
                <span>{s.label}</span>
              </label>
            ))}
          </fieldset>

          <label className={labelClass}>
            Their birth certificate
            <input
              required
              type="file"
              accept="application/pdf,image/jpeg,image/png"
              onChange={(e) => setBirthCertificate(e.target.files?.[0] ?? null)}
              className={inputClass}
            />
            <span className="mt-1 block text-xs font-normal text-zinc-500">PDF, JPEG or PNG, up to 10MB.</span>
          </label>
          <label className={labelClass}>
            Your own ID (optional, speeds up review)
            <input
              type="file"
              accept="application/pdf,image/jpeg,image/png"
              onChange={(e) => setGuardianId(e.target.files?.[0] ?? null)}
              className={inputClass}
            />
          </label>

          <label className="flex items-start gap-2 text-sm text-zinc-600 dark:text-zinc-400">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="mt-0.5 shrink-0 accent-rose-600"
            />
            <span>{CONSENT_STATEMENT}</span>
          </label>

          <p className="text-xs text-zinc-500">
            Documents you upload here are stored privately and are only ever seen by the small team that
            reviews them. They are never shown on the profile.
          </p>

          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={submitting || !agreed || scopes.length === 0} className={`w-fit ${btnPrimary}`}>
            {submitting ? "Submitting…" : "Submit for review"}
          </button>
        </form>
      )}
    </section>
  );
}

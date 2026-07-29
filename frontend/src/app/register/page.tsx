"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Check } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { ApiError, api } from "@/lib/api";
import { btnPrimary, btnSecondary, inputClass, labelClass } from "@/lib/ui";

export default function RegisterPage() {
  const { register, verifyEmail } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<"form" | "verify">("form");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"talent" | "recruiter">("talent");
  const [consentGiven, setConsentGiven] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [code, setCode] = useState("");
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [resent, setResent] = useState(false);
  const [resending, setResending] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!consentGiven) {
      setError("You must consent to data processing to create an account.");
      return;
    }
    setSubmitting(true);
    try {
      await register({ email, password, full_name: fullName, role, consent_given: consentGiven });
      setStep("verify");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerify(e: FormEvent) {
    e.preventDefault();
    setVerifyError(null);
    setVerifying(true);
    try {
      await verifyEmail(email, code);
      router.push("/dashboard");
    } catch (err) {
      setVerifyError(err instanceof ApiError ? err.message : "Could not verify that code.");
    } finally {
      setVerifying(false);
    }
  }

  async function handleResend() {
    setResending(true);
    setVerifyError(null);
    try {
      await api.resendVerification(email);
      setResent(true);
      setTimeout(() => setResent(false), 4000);
    } finally {
      setResending(false);
    }
  }

  if (step === "verify") {
    return (
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
        <span className="flex h-10 w-10 items-center justify-center rounded-sm bg-rose-600 text-sm font-black text-white">
          YT
        </span>
        <h1 className="mt-4 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
          Check your email
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          We sent a 6-digit code to <span className="font-semibold text-zinc-700 dark:text-zinc-300">{email}</span>.
          Enter it below to activate your account.
        </p>

        <form onSubmit={handleVerify} className="mt-8 flex flex-col gap-4">
          <label className={labelClass}>
            Verification code
            <input
              required
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              placeholder="123456"
              className={`${inputClass} text-center text-lg tracking-[0.5em]`}
            />
          </label>
          {verifyError && <p className="text-sm text-red-600">{verifyError}</p>}
          <button type="submit" disabled={verifying || code.length !== 6} className={`mt-2 ${btnPrimary}`}>
            {verifying ? "Verifying…" : "Verify email"}
          </button>
          <button type="button" onClick={handleResend} disabled={resending} className={btnSecondary}>
            {resending ? (
              "Sending…"
            ) : resent ? (
              <>
                <Check className="h-3.5 w-3.5" /> Code resent
              </>
            ) : (
              "Resend code"
            )}
          </button>
        </form>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
      <span className="flex h-10 w-10 items-center justify-center rounded-sm bg-rose-600 text-sm font-black text-white">
        YT
      </span>
      <h1 className="mt-4 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
        Create an account
      </h1>
      <p className="mt-1 text-sm text-zinc-500">Join as talent to audition, or as an organizer posting talent hunts.</p>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <fieldset className="flex gap-2">
          {(["talent", "recruiter"] as const).map((r) => (
            <button
              type="button"
              key={r}
              onClick={() => setRole(r)}
              className={`flex-1 rounded-md border-2 px-4 py-2.5 text-sm font-bold uppercase tracking-wide transition-colors ${
                role === r
                  ? "border-rose-600 bg-rose-600 text-white"
                  : "border-zinc-200 text-zinc-700 hover:border-rose-300 hover:bg-rose-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-rose-800 dark:hover:bg-rose-950"
              }`}
            >
              {r}
            </button>
          ))}
        </fieldset>

        <label className={labelClass}>
          Full name
          <input required value={fullName} onChange={(e) => setFullName(e.target.value)} className={inputClass} />
        </label>

        <label className={labelClass}>
          Email
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
        </label>

        <label className={labelClass}>
          Password
          <input
            required
            minLength={8}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
          />
        </label>

        <label className="flex items-start gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          <input
            type="checkbox"
            checked={consentGiven}
            onChange={(e) => setConsentGiven(e.target.checked)}
            className="mt-0.5 accent-rose-600"
          />
          I consent to my personal data being processed as described in the privacy policy, in
          line with the Personal Data Protection Act No. 9 of 2022.
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" disabled={submitting} className={`mt-2 ${btnPrimary}`}>
          {submitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-zinc-500">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-rose-600 hover:underline">
          Log in
        </Link>
      </p>
    </main>
  );
}

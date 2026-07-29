"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Check } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { ApiError, api } from "@/lib/api";
import { btnPrimary, btnSecondary, inputClass, labelClass } from "@/lib/ui";

export default function LoginPage() {
  const { login, verifyEmail } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [needsVerification, setNeedsVerification] = useState(false);

  const [code, setCode] = useState("");
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [resent, setResent] = useState(false);
  const [resending, setResending] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError && err.status === 403 && err.message.toLowerCase().includes("verify")) {
        setNeedsVerification(true);
      } else {
        setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      }
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

  if (needsVerification) {
    return (
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
        <span className="flex h-10 w-10 items-center justify-center rounded-sm bg-rose-600 text-sm font-black text-white">
          YT
        </span>
        <h1 className="mt-4 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
          Verify your email
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Your account isn&apos;t verified yet. Enter the code we sent to{" "}
          <span className="font-semibold text-zinc-700 dark:text-zinc-300">{email}</span>, or send a new one.
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
          <button
            type="button"
            onClick={() => setNeedsVerification(false)}
            className="text-sm font-semibold text-zinc-500 hover:underline"
          >
            ← Back to log in
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
        Log in
      </h1>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
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
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" disabled={submitting} className={`mt-2 ${btnPrimary}`}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p className="mt-6 text-sm text-zinc-500">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-semibold text-rose-600 hover:underline">
          Sign up
        </Link>
      </p>
    </main>
  );
}

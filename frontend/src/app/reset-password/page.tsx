"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { ApiError, api } from "@/lib/api";
import { btnPrimary, btnSecondary, inputClass, labelClass } from "@/lib/ui";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}

function ResetPasswordForm() {
  const { resetPassword } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [resent, setResent] = useState(false);
  const [resending, setResending] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    setSubmitting(true);
    try {
      await resetPassword(email, code, newPassword);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reset your password.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    if (!email) return;
    setResending(true);
    setError(null);
    try {
      await api.forgotPassword(email);
      setResent(true);
      setTimeout(() => setResent(false), 4000);
    } finally {
      setResending(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
      <span className="flex h-10 w-10 items-center justify-center rounded-sm bg-rose-600 text-sm font-black text-white">
        YT
      </span>
      <h1 className="mt-4 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
        Reset password
      </h1>
      <p className="mt-1 text-sm text-zinc-500">
        Enter the code we emailed you along with your new password.
      </p>

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
          Reset code
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

        <label className={labelClass}>
          New password
          <input
            required
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className={inputClass}
          />
        </label>

        <label className={labelClass}>
          Confirm new password
          <input
            required
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className={inputClass}
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" disabled={submitting || code.length !== 6} className={`mt-2 ${btnPrimary}`}>
          {submitting ? "Resetting…" : "Reset password"}
        </button>
        <button type="button" onClick={handleResend} disabled={resending || !email} className={btnSecondary}>
          {resending ? "Sending…" : resent ? "Code resent" : "Resend code"}
        </button>
      </form>

      <p className="mt-6 text-sm text-zinc-500">
        <Link href="/login" className="font-semibold text-rose-600 hover:underline">
          ← Back to log in
        </Link>
      </p>
    </main>
  );
}

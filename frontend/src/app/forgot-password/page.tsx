"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ApiError, api } from "@/lib/api";
import { btnPrimary, inputClass, labelClass } from "@/lib/ui";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (sent) {
    return (
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
        <span className="flex h-10 w-10 items-center justify-center rounded-sm bg-rose-600 text-sm font-black text-white">
          YT
        </span>
        <h1 className="mt-4 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
          Check your email
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          If an account exists for{" "}
          <span className="font-semibold text-zinc-700 dark:text-zinc-300">{email}</span>, we&apos;ve sent a
          6-digit reset code. It expires in 15 minutes.
        </p>
        <button
          onClick={() => router.push(`/reset-password?email=${encodeURIComponent(email)}`)}
          className={`mt-8 ${btnPrimary}`}
        >
          Enter reset code
        </button>
        <Link href="/login" className="mt-4 text-sm font-semibold text-zinc-500 hover:underline">
          ← Back to log in
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
      <span className="flex h-10 w-10 items-center justify-center rounded-sm bg-rose-600 text-sm font-black text-white">
        YT
      </span>
      <h1 className="mt-4 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 dark:text-zinc-50">
        Forgot password
      </h1>
      <p className="mt-1 text-sm text-zinc-500">
        Enter your account email and we&apos;ll send you a code to reset your password.
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

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" disabled={submitting} className={`mt-2 ${btnPrimary}`}>
          {submitting ? "Sending…" : "Send reset code"}
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

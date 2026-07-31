"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import TalentDashboard from "@/components/dashboard/TalentDashboard";
import RecruiterDashboard from "@/components/dashboard/RecruiterDashboard";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.push("/login");
      return;
    }
    if (user.role === "admin") {
      router.push("/admin");
    }
  }, [loading, user, router]);

  if (loading || !user || user.role === "admin") {
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        <p className="text-sm text-zinc-500">Loading…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
      <h1 className="font-heading text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Dashboard</h1>
      <div className="mt-8">
        {user.role === "talent" ? <TalentDashboard /> : user.role === "recruiter" ? <RecruiterDashboard /> : null}
      </div>
    </main>
  );
}

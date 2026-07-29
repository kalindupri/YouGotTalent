"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import TalentDashboard from "@/components/dashboard/TalentDashboard";
import RecruiterDashboard from "@/components/dashboard/RecruiterDashboard";
import AdminDashboard from "@/components/dashboard/AdminDashboard";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        <p className="text-sm text-zinc-500">Loading…</p>
      </main>
    );
  }

  const isAdmin = user.role === "admin";

  return (
    <main className={`mx-auto w-full flex-1 px-6 py-16 ${isAdmin ? "max-w-5xl" : "max-w-3xl"}`}>
      <h1 className="font-heading text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
        {isAdmin ? "Admin Dashboard" : "Dashboard"}
      </h1>
      <div className="mt-8">
        {user.role === "talent" ? (
          <TalentDashboard />
        ) : user.role === "recruiter" ? (
          <RecruiterDashboard />
        ) : isAdmin ? (
          <AdminDashboard />
        ) : null}
      </div>
    </main>
  );
}

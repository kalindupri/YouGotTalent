"use client";

import UserManagement from "@/components/admin/UserManagement";

export default function AdminUsersPage() {
  return (
    <div>
      <h1 className="font-heading text-3xl font-black text-zinc-900 dark:text-zinc-50">Users</h1>
      <p className="mt-1 text-sm text-zinc-500">Search, review, and suspend accounts.</p>
      <div className="mt-6">
        <UserManagement />
      </div>
    </div>
  );
}
